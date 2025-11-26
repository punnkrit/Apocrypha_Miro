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
            if update.get("type") == "add_to_context":
                new_nodes = update.get("nodes", [])
                added_count = 0
                for n in new_nodes:
                    # Avoid duplicates
                    if not any(existing["id"] == n["id"] for existing in st.session_state.context_nodes):
                        # Resolve files
                        files = map_node_to_files(n["id"])
                        node_with_files = {**n, "files": files}
                        st.session_state.context_nodes.append(node_with_files)
                        
                        # Add system notification (visible only in chat history, not popped up)
                        st.session_state.messages.append({
                            "role": "system",
                            "content": f"📂 Added {n['label']} to context ({len(files)} files found)."
                        })
                        added_count += 1
                
                if added_count > 0:
                    st.rerun()

with col_chat:
    st.subheader("Chat")
    
    # Context Display
    if st.session_state.context_nodes:
        with st.expander("📚 Active Context", expanded=True):
            for node in st.session_state.context_nodes:
                st.markdown(f"**{node['label']}**")
                if node.get('files'):
                    for f in node['files']:
                        st.caption(f"• {f}")
                else:
                    st.caption("(No files found)")
            
            if st.button("Clear Context"):
                st.session_state.context_nodes = []
                st.rerun()

    # Chat Interface
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

    if prompt := st.chat_input("Ask about the files..."):
        # User message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        # RAG / Search Logic
        relevant_docs = []
        if st.session_state.context_nodes:
            folder_names = [n['label'] for n in st.session_state.context_nodes]
            relevant_docs = search_files(prompt, st.session_state.records, k=50, context_folders=folder_names)
        else:
            # Search all
            relevant_docs = search_files(prompt, st.session_state.records, k=50)

        # Highlight logic
        high_relevance_docs = []
        if relevant_docs:
            # Only highlight nodes for documents with score > 3.0
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
