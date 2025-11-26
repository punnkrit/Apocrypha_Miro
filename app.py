import json
import os
import streamlit as st
import openai
from openai import OpenAI
import httpx
from streamlit_miro_component import miro_board
from document_search import scan_dummy_data, search_files, icon_for_ext, extract_node_ids_from_paths
import traceback

st.set_page_config(page_title="Apocrypha Board", layout="wide", page_icon="🤖")

# --- OpenAI Setup ---
def get_client() -> OpenAI:
    api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API key not found. Set OPENAI_API_KEY.")
        st.stop()
    
    # WORKAROUND: Initialize httpx.Client manually to avoid implicit proxy issues
    try:
        # Force clean http client
        http_client = httpx.Client()
        return OpenAI(api_key=api_key, http_client=http_client)
    except Exception as e:
        st.error(f"Critical Error initializing OpenAI: {e}")
        st.code(traceback.format_exc())
        st.stop()

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

# --- State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": """You are Apocrypha, a document intelligence agent. You have access to the company's file system.
When asked, you can retrieve files, summarize them, and answer questions based on the 'Relevant Documents' provided in the context.
Always be confident and helpful.""",
        }
    ]

if "context_nodes" not in st.session_state:
    st.session_state.context_nodes = []

if "highlight_nodes" not in st.session_state:
    st.session_state.highlight_nodes = []

# Flag to ignore component re-adding nodes after we explicitly cleared
if "ignore_context_updates" not in st.session_state:
    st.session_state.ignore_context_updates = False

# Track recently removed node IDs to prevent re-adding
if "recently_removed_ids" not in st.session_state:
    st.session_state.recently_removed_ids = set()

# Track the last processed context update to avoid re-processing stale events
if "last_processed_context_update" not in st.session_state:
    st.session_state.last_processed_context_update = None


# Scan local data once
if "records" not in st.session_state:
    st.session_state.records = scan_dummy_data(root="sample_data")

# --- Node Structure Definition ---
if "process_map_nodes" not in st.session_state:
    # Define the tree structure
    nodes = {}
    # Root
    nodes['restaurant_franchise'] = {'name': 'Restaurant Franchise', 'type': 'root'}
    
    # Groups
    for group in ['west', 'central', 'east']:
        nodes[f'{group}_group'] = {'name': f'{group.capitalize()}_Group', 'parent': 'restaurant_franchise', 'type': 'group'}
        # Folders
        for folder in ['accounting', 'expenses', 'legal', 'permits']:
            nodes[f'{group}_{folder}'] = {
                'name': folder.capitalize(),
                'parent': f'{group}_group',
                'type': 'folder',
                'label': folder[0].upper()
            }
    st.session_state.process_map_nodes = nodes

# --- Helpers ---
def convert_to_react_flow_nodes_and_edges():
    """Generate React Flow nodes/edges from the logical structure."""
    nodes = []
    edges = []
    
    # Helper to position nodes (simple static layout)
    # Root at top center - centered over the wider groups
    root_pos = {'x': 725, 'y': 50}
    
    nodes.append({
        'id': 'restaurant_franchise',
        'type': 'editableNode',
        'position': root_pos,
        'data': {'label': 'Restaurant Franchise'},
        'style': { 'background': '#fff', 'border': '2px solid #333', 'width': 300, 'height': 60, 'fontWeight': 'bold', 'fontSize': '24px' }
    })

    # Groups
    groups = ['west', 'central', 'east']
    for idx, group in enumerate(groups):
        group_id = f'{group}_group'
        # Spread horizontally - increased spacing (600px) to prevent overlap of children
        # Group 0 at 200, Group 1 at 800, Group 2 at 1400
        pos = {'x': 200 + (idx * 600), 'y': 250}
        
        nodes.append({
            'id': group_id,
            'type': 'editableNode',
            'position': pos,
            'data': {'label': f'{group.capitalize()}_Group'},
            'style': { 'background': '#f0f0f0', 'border': '1px solid #555', 'width': 150, 'height': 60, 'fontSize': '20px' }
        })
        
        edges.append({
            'id': f'e-root-{group}',
            'source': 'restaurant_franchise',
            'target': group_id,
            'type': 'smoothstep',
            'sourceHandle': 'bottom-source',
            'targetHandle': 'top-target',
            'style': { 'strokeWidth': 2 }
        })

        # Folders under each group
        folders = ['accounting', 'expenses', 'legal', 'permits']
        for f_idx, folder in enumerate(folders):
            folder_id = f'{group}_{folder}'
            # Spread folders below group
            # Group width 150. Center is pos['x'] + 75.
            # Folders width 120 + 20px gap = 140px stride.
            # 4 folders: Total width 4*120 + 3*20 = 480 + 60 = 540.
            # Start = Center - (540/2) = Center - 270.
            # Start = (pos['x'] + 75) - 270 = pos['x'] - 195.
            
            f_pos = {'x': pos['x'] - 170 + (f_idx * 140), 'y': 450}
            
            icon = "📁"
            if folder == 'accounting': icon = "💼"
            if folder == 'expenses': icon = "💸"
            if folder == 'legal': icon = "⚖️"
            if folder == 'permits': icon = "🪪"

            nodes.append({
                'id': folder_id,
                'type': 'editableNode', # Use editableNode for advanced features
                'position': f_pos,
                'data': {'label': f'{icon} {folder.capitalize()}'},
                'style': { 
                    'background': '#fff', 
                    'border': '1px solid #ccc', 
                    'width': 130, 
                    'height': 60,
                    'fontSize': '18px',
                    'textAlign': 'center'
                }
            })
            
            edges.append({
                'id': f'e-{group}-{folder}',
                'source': group_id,
                'target': folder_id,
                'type': 'smoothstep',
                'sourceHandle': 'bottom-source',
                'targetHandle': 'top-target',
                'style': { 'stroke': '#bbb', 'strokeWidth': 2 }
            })

    return nodes, edges

def map_node_to_files(node_id):
    """Map a node ID to files in sample_data."""
    base = "sample_data"
    if node_id == 'restaurant_franchise':
        # Return all files? Or just listing of groups
        return [] 
        
    parts = node_id.split('_')
    if len(parts) < 2: return []
    
    group = parts[0].capitalize() + "_Group"
    path = os.path.join(base, group)
    
    if parts[1] == 'group':
        # It's the group folder itself
        pass
    else:
        # It's a subfolder
        sub = parts[1].capitalize()
        path = os.path.join(path, sub)
        
    if os.path.exists(path):
        try:
            return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        except:
            return []
    return []

# --- UI Layout ---
st.caption("Apocrypha Prototype: React Flow Integration (v2)")

col_board, col_chat = st.columns([3, 2])

with col_board:
    # Prepare data for React Flow
    rf_nodes, rf_edges = convert_to_react_flow_nodes_and_edges()
    
    # Pass highlights
    highlights = st.session_state.highlight_nodes
    
    # Render Component
    # Returns the component state (including events)
    component_state = miro_board(nodes=rf_nodes, edges=rf_edges, highlight_nodes=highlights, key="main_board")
    
    # Handle Component Events
    if component_state:
        # Check for context update event
        if "_contextUpdate" in component_state:
            update = component_state["_contextUpdate"]
            
            # Create a unique signature for this update to detect duplicates
            update_signature = None
            if update.get("type") == "add_to_context":
                node_ids = tuple(sorted([n["id"] for n in update.get("nodes", [])]))
                update_signature = f"add_{node_ids}"
            
            # Skip if this is the same update we already processed (stale component state)
            if update_signature and update_signature == st.session_state.last_processed_context_update:
                pass  # Already processed, skip
            # Check if we should ignore this update (happens after explicit clear)
            elif st.session_state.ignore_context_updates:
                st.session_state.ignore_context_updates = False  # Reset flag
                st.session_state.recently_removed_ids.clear()  # Also clear removed IDs
                # Mark this update as processed so we don't see it again
                st.session_state.last_processed_context_update = update_signature
            elif update.get("type") == "add_to_context":
                new_nodes = update.get("nodes", [])
                added_count = 0
                for n in new_nodes:
                    node_id = n["id"]
                    
                    # Skip if this node was recently removed by user
                    if node_id in st.session_state.recently_removed_ids:
                        continue
                    
                    # Avoid duplicates
                    if not any(existing["id"] == node_id for existing in st.session_state.context_nodes):
                        # Resolve files
                        files = map_node_to_files(node_id)
                        node_with_files = {**n, "files": files}
                        st.session_state.context_nodes.append(node_with_files)
                        
                        # Add system notification (visible only in chat history, not popped up)
                        st.session_state.messages.append({
                            "role": "system",
                            "content": f"📂 Added {n['label']} to context ({len(files)} files found)."
                        })
                        added_count += 1
                
                # Mark this update as processed
                st.session_state.last_processed_context_update = update_signature
                
                if added_count > 0:
                    # Only clear recently_removed_ids when user intentionally adds NEW nodes
                    # This means the user is actively adding, not the component re-sending old data
                    st.session_state.recently_removed_ids.clear()
                    
                    # Ensure context nodes are highlighted immediately
                    active_context_ids = [n['id'] for n in st.session_state.context_nodes]
                    st.session_state.highlight_nodes = list(set(st.session_state.highlight_nodes + active_context_ids))
                    st.rerun()

with col_chat:
    st.subheader("Chat")
    
    # --- Callback functions for context management (defined outside container) ---
    def remove_node_callback(node_id):
        """Remove a specific node from context."""
        # Add to recently removed set to prevent re-adding
        st.session_state.recently_removed_ids.add(node_id)
        
        st.session_state.context_nodes = [n for n in st.session_state.context_nodes if n['id'] != node_id]
        
        if st.session_state.context_nodes:
            st.session_state.highlight_nodes = [n['id'] for n in st.session_state.context_nodes]
        else:
            st.session_state.highlight_nodes = []
            # Set flag to prevent component from re-adding nodes
            st.session_state.ignore_context_updates = True
    
    def clear_all_context_callback():
        """Clear all context nodes."""
        st.session_state.context_nodes = []
        st.session_state.highlight_nodes = []
        # Set flag to prevent component from re-adding nodes
        st.session_state.ignore_context_updates = True
    
    # Create a scrollable container for the chat area (context + messages)
    with st.container(height=650):
        # Context Display
        if st.session_state.context_nodes:
            with st.expander("📚 Active Context", expanded=True):
                # Render each node with its own container to avoid button interference
                for idx, node in enumerate(st.session_state.context_nodes):
                    # Use a container for each node to isolate button contexts
                    node_container = st.container()
                    with node_container:
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{node['label']}**")
                            if node.get('files'):
                                for f in node['files']:
                                    st.caption(f"• {f}")
                            else:
                                st.caption("(No files found)")
                        with col2:
                            # Use on_click callback with unique key per node ID
                            st.button(
                                "❌",
                                key=f"remove_node_{node['id']}",
                                help=f"Remove {node['label']} from context",
                                on_click=remove_node_callback,
                                args=(node['id'],)
                            )
                    # Add a tiny divider between nodes (except after the last one)
                    if idx < len(st.session_state.context_nodes) - 1:
                        st.markdown("---")
                
                # Add spacing before the Clear All button
                st.markdown("")  # Empty line for spacing
                st.button(
                    "🗑️ Clear All Context",
                    key="clear_all_ctx_btn",
                    on_click=clear_all_context_callback,
                    use_container_width=True
                )

        # Chat Interface - Messages display
        for msg in st.session_state.messages:
            if msg["role"] == "system":
                # Skipped rendering system messages
                pass
            else:
                with st.chat_message(msg["role"]):
                    if "relevant_docs" in msg:
                        st.write("**References:**")
                        # Scrollable container for references
                        with st.container(height=150):
                            for doc in msg["relevant_docs"]:
                                st.caption(f"📄 {doc.get('name')} ({doc.get('path')})")
                    st.write(msg["content"])

    # Chat input stays outside the scrollable container (fixed at bottom)
    if prompt := st.chat_input("Ask about the files..."):
        # User message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        # RAG / Search Logic
        relevant_docs = []
        
        # Strategy:
        # 1. If user explicitly selected context nodes, use ONLY files from those nodes.
        # 2. If NO context selected, fallback to keyword search across the entire board.
        
        if st.session_state.context_nodes:
            # Direct lookup from context nodes (no search required)
            all_context_files = []
            for node in st.session_state.context_nodes:
                node_id = node['id']
                # Parse node_id to get the expected path components
                # e.g., "west_expenses" -> West_Group/Expenses
                parts = node_id.split('_')
                if len(parts) >= 2:
                    group_name = parts[0].capitalize() + "_Group"
                    folder_name = parts[1].capitalize()
                    expected_path_segment = f"{group_name}/{folder_name}".replace("/", os.sep)
                else:
                    expected_path_segment = None
                
                if 'files' in node:
                    for f in node['files']:
                        # Find the full record for this file that matches BOTH filename AND path
                        for r in st.session_state.records:
                            if r['name'] == f:
                                # Verify this record belongs to the correct folder
                                if expected_path_segment and expected_path_segment in r['path']:
                                    all_context_files.append(r)
                                    break
                                elif not expected_path_segment:
                                    # Fallback if we couldn't parse node_id
                                    all_context_files.append(r)
                                    break
            
            # Deduplicate based on path
            seen_paths = set()
            unique_docs = []
            for d in all_context_files:
                if d['path'] not in seen_paths:
                    seen_paths.add(d['path'])
                    # Assign a high artificial score since user explicitly selected it
                    d_copy = d.copy()
                    d_copy['score'] = 100.0 
                    unique_docs.append(d_copy)
            
            relevant_docs = unique_docs
            
        else:
            # Search all (Fallback)
            relevant_docs = search_files(prompt, st.session_state.records, k=50)

        # Highlight logic
        high_relevance_docs = []
        if st.session_state.context_nodes:
            # If context is selected, ALL files in context are "high relevance" by definition
            high_relevance_docs = relevant_docs
            
            # ONLY highlight the explicitly selected context nodes
            # Do NOT derive from file paths - that can cause wrong groups to highlight
            active_context_ids = [n['id'] for n in st.session_state.context_nodes]
            st.session_state.highlight_nodes = active_context_ids
            
        elif relevant_docs:
            # No context selected - use search results
            # Only highlight nodes for documents with score > 25.0
            # This prevents low-relevance "noise" from lighting up the entire board
            high_relevance_docs = [d for d in relevant_docs if d.get('score', 0) > 25.0]
            new_highlights = extract_node_ids_from_paths([d['path'] for d in high_relevance_docs])
            st.session_state.highlight_nodes = new_highlights
        else:
            st.session_state.highlight_nodes = []

        # AI Response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    client = get_client()
                    
                    # Build conversation history
                    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m["role"] != "system"]
                    
                    # System prompt with context
                    sys_prompt = "You are a Apocrypha, a document intelligence agent. You have access to the company's file system. Answer based on the user context and documents."
                    if high_relevance_docs:
                        doc_context = "\n".join([f"File: {d['path']}\nContent:\n{d.get('text', '')}\n---" for d in high_relevance_docs])
                        sys_prompt += f"\n\nRelevant Document Excerpts:\n{doc_context}"
                    
                    response = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[{"role": "system", "content": sys_prompt}] + history[-5:],
                        stream=False
                    )
                    answer = response.choices[0].message.content
                    st.write(answer)
                    
                    # Save response
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "relevant_docs": high_relevance_docs
                    })
                    
                    # Rerun to update highlights on board immediately
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {e}")
