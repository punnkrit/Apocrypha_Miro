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

# Track if we're currently processing a query (for showing spinner inside container)
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

# Store pending prompt for processing after rerun
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# Scan local data once
if "records" not in st.session_state:
    st.session_state.records = scan_dummy_data(root="sample_data")

# --- Industry Selection ---
if "selected_industry" not in st.session_state:
    st.session_state.selected_industry = "fnb"  # Default to F&B

# --- Node Structure Definition (Dynamic based on industry) ---
def get_fnb_nodes():
    """Generate Restaurant Franchise node structure."""
    nodes = {}
    nodes['restaurant_franchise'] = {'name': 'Restaurant Franchise', 'type': 'root'}
    
    for group in ['west', 'central', 'east']:
        nodes[f'{group}_group'] = {'name': f'{group.capitalize()}_Group', 'parent': 'restaurant_franchise', 'type': 'group'}
        for folder in ['accounting', 'expenses', 'legal', 'permits']:
            nodes[f'{group}_{folder}'] = {
                'name': folder.capitalize(),
                'parent': f'{group}_group',
                'type': 'folder',
                'label': folder[0].upper()
            }
    return nodes

def get_legal_nodes():
    """Generate Legal Firm node structure."""
    nodes = {}
    nodes['legal_firm'] = {'name': 'Legal Firm', 'type': 'root'}
    
    # Practice areas with their matters
    practice_areas = {
        'corporate_law': ['techcorp_acquisition', 'globalretail_ipo'],
        'litigation': ['smith_v_megacorp', 'contractdispute_abcvxyz'],
        'real_estate': ['downtown_tower_development', 'office_lease_negotiation'],
        'intellectual_property': ['patent_portfolio_biotech', 'trademark_dispute_fashion'],
        'employment_law': ['executive_compensation_review', 'workplace_investigation'],
    }
    
    for area, matters in practice_areas.items():
        area_name = area.replace('_', ' ').title().replace(' ', '_')
        nodes[area] = {'name': area_name, 'parent': 'legal_firm', 'type': 'practice_area'}
        for matter in matters:
            nodes[f'{area}_{matter}'] = {
                'name': matter.replace('_', ' ').title(),
                'parent': area,
                'type': 'matter',
            }
    return nodes

def update_process_map_nodes():
    """Update the node structure based on selected industry."""
    if st.session_state.selected_industry == "fnb":
        st.session_state.process_map_nodes = get_fnb_nodes()
    else:
        st.session_state.process_map_nodes = get_legal_nodes()

# Initialize nodes
if "process_map_nodes" not in st.session_state:
    update_process_map_nodes()

# --- Helpers ---
def convert_to_react_flow_nodes_and_edges():
    """Generate React Flow nodes/edges from the logical structure based on selected industry."""
    if st.session_state.selected_industry == "fnb":
        return convert_fnb_nodes_and_edges()
    else:
        return convert_legal_nodes_and_edges()

def convert_fnb_nodes_and_edges():
    """Generate React Flow nodes/edges for Restaurant Franchise."""
    nodes = []
    edges = []
    
    root_pos = {'x': 725, 'y': 50}
    
    nodes.append({
        'id': 'restaurant_franchise',
        'type': 'editableNode',
        'position': root_pos,
        'data': {'label': '🍽️ Restaurant Franchise'},
        'style': { 'background': '#fff', 'border': '2px solid #333', 'width': 300, 'height': 60, 'fontWeight': 'bold', 'fontSize': '24px' }
    })

    groups = ['west', 'central', 'east']
    for idx, group in enumerate(groups):
        group_id = f'{group}_group'
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

        folders = ['accounting', 'expenses', 'legal', 'permits']
        for f_idx, folder in enumerate(folders):
            folder_id = f'{group}_{folder}'
            f_pos = {'x': pos['x'] - 170 + (f_idx * 140), 'y': 450}
            
            icon = "📁"
            if folder == 'accounting': icon = "💼"
            if folder == 'expenses': icon = "💸"
            if folder == 'legal': icon = "⚖️"
            if folder == 'permits': icon = "🪪"

            nodes.append({
                'id': folder_id,
                'type': 'editableNode',
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

def convert_legal_nodes_and_edges():
    """Generate React Flow nodes/edges for Legal Firm."""
    nodes = []
    edges = []
    
    root_pos = {'x': 725, 'y': 50}
    
    nodes.append({
        'id': 'legal_firm',
        'type': 'editableNode',
        'position': root_pos,
        'data': {'label': '⚖️ Legal Firm'},
        'style': { 'background': '#fff', 'border': '2px solid #1a365d', 'width': 250, 'height': 60, 'fontWeight': 'bold', 'fontSize': '24px' }
    })

    # Practice areas with icons and their specific matters
    practice_areas = [
        ('corporate_law', '🏢 Corporate Law', [
            ('techcorp_acquisition', 'TechCorp Acquisition'),
            ('globalretail_ipo', 'GlobalRetail IPO'),
        ]),
        ('litigation', '⚔️ Litigation', [
            ('smith_v_megacorp', 'Smith v MegaCorp'),
            ('contractdispute_abcvxyz', 'Contract Dispute'),
        ]),
        ('real_estate', '🏗️ Real Estate', [
            ('downtown_tower_development', 'Tower Development'),
            ('office_lease_negotiation', 'Office Lease'),
        ]),
        ('intellectual_property', '💡 IP', [
            ('patent_portfolio_biotech', 'Patent Portfolio'),
            ('trademark_dispute_fashion', 'Trademark Dispute'),
        ]),
        ('employment_law', '👥 Employment', [
            ('executive_compensation_review', 'Exec Compensation'),
            ('workplace_investigation', 'Workplace Investigation'),
        ]),
    ]
    
    for idx, (area_id, area_label, matters) in enumerate(practice_areas):
        # Position practice areas horizontally
        area_pos = {'x': 100 + (idx * 320), 'y': 220}
        
        nodes.append({
            'id': area_id,
            'type': 'editableNode',
            'position': area_pos,
            'data': {'label': area_label},
            'style': { 'background': '#e8f4f8', 'border': '1px solid #2c5282', 'width': 180, 'height': 55, 'fontSize': '16px' }
        })
        
        edges.append({
            'id': f'e-root-{area_id}',
            'source': 'legal_firm',
            'target': area_id,
            'type': 'smoothstep',
            'sourceHandle': 'bottom-source',
            'targetHandle': 'top-target',
            'style': { 'strokeWidth': 2, 'stroke': '#2c5282' }
        })
        
        # Matters under each practice area - positioned horizontally like F&B folders
        num_matters = len(matters)
        matter_width = 150
        matter_gap = 20
        total_matters_width = (num_matters * matter_width) + ((num_matters - 1) * matter_gap)
        # Center matters under the practice area (area width is 180)
        area_center_x = area_pos['x'] + 90  # 180/2 = 90
        start_x = area_center_x - (total_matters_width / 2)
        
        for m_idx, (matter_id, matter_label) in enumerate(matters):
            full_matter_id = f'{area_id}_{matter_id}'
            # Position matters horizontally under each practice area
            m_pos = {'x': start_x + (m_idx * (matter_width + matter_gap)), 'y': 380}
            
            nodes.append({
                'id': full_matter_id,
                'type': 'editableNode',
                'position': m_pos,
                'data': {'label': f'📋 {matter_label}'},
                'style': { 
                    'background': '#fff', 
                    'border': '1px solid #a0aec0', 
                    'width': matter_width, 
                    'height': 55,
                    'fontSize': '13px',
                    'textAlign': 'center'
                }
            })
            
            # Each matter connects to its parent practice area
            edges.append({
                'id': f'e-{area_id}-to-{matter_id}',
                'source': area_id,
                'target': full_matter_id,
                'type': 'smoothstep',
                'sourceHandle': 'bottom-source',
                'targetHandle': 'top-target',
                'style': { 'stroke': '#a0aec0', 'strokeWidth': 2 }
            })

    return nodes, edges

def map_node_to_files(node_id):
    """Map a node ID to files in sample_data based on current industry."""
    base = "sample_data"
    
    if st.session_state.selected_industry == "fnb":
        return map_fnb_node_to_files(node_id, base)
    else:
        return map_legal_node_to_files(node_id, base)

def map_fnb_node_to_files(node_id, base):
    """Map F&B node ID to files."""
    if node_id == 'restaurant_franchise':
        return []
        
    parts = node_id.split('_')
    if len(parts) < 2: return []
    
    group = parts[0].capitalize() + "_Group"
    path = os.path.join(base, "Restaurant_Franchise", group)
    
    if parts[1] == 'group':
        pass
    else:
        sub = parts[1].capitalize()
        path = os.path.join(path, sub)
        
    if os.path.exists(path):
        try:
            return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        except:
            return []
    return []

def map_legal_node_to_files(node_id, base):
    """Map Legal Firm node ID to files."""
    if node_id == 'legal_firm':
        return []
    
    # Practice area IDs: corporate_law, litigation, etc.
    practice_areas = ['corporate_law', 'litigation', 'real_estate', 'intellectual_property', 'employment_law']
    
    # Check if it's a practice area (no matter suffix)
    if node_id in practice_areas:
        return []  # Practice areas don't have files directly
    
    # It's a matter - parse the ID
    # Format: {practice_area}_{matter_id}
    # e.g., corporate_law_techcorp_acquisition
    
    # Map node IDs to folder names
    matter_folder_map = {
        'corporate_law_techcorp_acquisition': 'Corporate_Law/TechCorp_Acquisition',
        'corporate_law_globalretail_ipo': 'Corporate_Law/GlobalRetail_IPO',
        'litigation_smith_v_megacorp': 'Litigation/Smith_v_MegaCorp',
        'litigation_contractdispute_abcvxyz': 'Litigation/ContractDispute_ABCvXYZ',
        'real_estate_downtown_tower_development': 'Real_Estate/Downtown_Tower_Development',
        'real_estate_office_lease_negotiation': 'Real_Estate/Office_Lease_Negotiation',
        'intellectual_property_patent_portfolio_biotech': 'Intellectual_Property/Patent_Portfolio_BioTech',
        'intellectual_property_trademark_dispute_fashion': 'Intellectual_Property/Trademark_Dispute_Fashion',
        'employment_law_executive_compensation_review': 'Employment_Law/Executive_Compensation_Review',
        'employment_law_workplace_investigation': 'Employment_Law/Workplace_Investigation',
    }
    
    if node_id in matter_folder_map:
        path = os.path.join(base, "Legal_Firm", matter_folder_map[node_id])
        if os.path.exists(path):
            try:
                return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            except:
                return []
    
    return []

def get_expected_path_segment(node_id):
    """Get the expected path segment for a node ID based on current industry."""
    if st.session_state.selected_industry == "fnb":
        # F&B: west_expenses -> Restaurant_Franchise/West_Group/Expenses
        parts = node_id.split('_')
        if len(parts) >= 2 and parts[1] != 'group':
            group_name = parts[0].capitalize() + "_Group"
            folder_name = parts[1].capitalize()
            return f"Restaurant_Franchise{os.sep}{group_name}{os.sep}{folder_name}"
        return None
    else:
        # Legal: Use the matter_folder_map
        matter_folder_map = {
            'corporate_law_techcorp_acquisition': 'Legal_Firm/Corporate_Law/TechCorp_Acquisition',
            'corporate_law_globalretail_ipo': 'Legal_Firm/Corporate_Law/GlobalRetail_IPO',
            'litigation_smith_v_megacorp': 'Legal_Firm/Litigation/Smith_v_MegaCorp',
            'litigation_contractdispute_abcvxyz': 'Legal_Firm/Litigation/ContractDispute_ABCvXYZ',
            'real_estate_downtown_tower_development': 'Legal_Firm/Real_Estate/Downtown_Tower_Development',
            'real_estate_office_lease_negotiation': 'Legal_Firm/Real_Estate/Office_Lease_Negotiation',
            'intellectual_property_patent_portfolio_biotech': 'Legal_Firm/Intellectual_Property/Patent_Portfolio_BioTech',
            'intellectual_property_trademark_dispute_fashion': 'Legal_Firm/Intellectual_Property/Trademark_Dispute_Fashion',
            'employment_law_executive_compensation_review': 'Legal_Firm/Employment_Law/Executive_Compensation_Review',
            'employment_law_workplace_investigation': 'Legal_Firm/Employment_Law/Workplace_Investigation',
        }
        if node_id in matter_folder_map:
            return matter_folder_map[node_id].replace("/", os.sep)
        return None

# --- UI Layout ---
st.caption("Apocrypha Prototype: React Flow Integration (v2)")

# Industry selector callbacks
def select_fnb():
    if st.session_state.selected_industry != "fnb":
        st.session_state.selected_industry = "fnb"
        update_process_map_nodes()
        # Clear context when switching industries
        st.session_state.context_nodes = []
        st.session_state.highlight_nodes = []

def select_legal():
    if st.session_state.selected_industry != "legal":
        st.session_state.selected_industry = "legal"
        update_process_map_nodes()
        # Clear context when switching industries
        st.session_state.context_nodes = []
        st.session_state.highlight_nodes = []

col_board, col_chat = st.columns([3, 2])

with col_board:
    # Industry selector buttons
    ind_col1, ind_col2, ind_col3 = st.columns([1, 1, 3])
    with ind_col1:
        fnb_selected = st.session_state.selected_industry == "fnb"
        st.button(
            "🍽️ F&B",
            key="btn_fnb",
            type="primary" if fnb_selected else "secondary",
            on_click=select_fnb,
            use_container_width=True
        )
    with ind_col2:
        legal_selected = st.session_state.selected_industry == "legal"
        st.button(
            "⚖️ Legal",
            key="btn_legal",
            type="primary" if legal_selected else "secondary",
            on_click=select_legal,
            use_container_width=True
        )
    
    # Prepare data for React Flow
    rf_nodes, rf_edges = convert_to_react_flow_nodes_and_edges()
    
    # Pass highlights
    highlights = st.session_state.highlight_nodes
    
    # Render Component with unique key per industry to force re-render
    component_key = f"main_board_{st.session_state.selected_industry}"
    component_state = miro_board(nodes=rf_nodes, edges=rf_edges, highlight_nodes=highlights, key=component_key)
    
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
                # Do NOT store the signature here - we want to allow re-adding the same nodes later
            elif update.get("type") == "add_to_context":
                new_nodes = update.get("nodes", [])
                
                # Check if this is a NEW selection (different from last processed)
                # If so, clear recently_removed_ids to allow re-adding previously removed nodes
                is_new_selection = (update_signature != st.session_state.last_processed_context_update)
                if is_new_selection:
                    st.session_state.recently_removed_ids.clear()
                
                added_count = 0
                for n in new_nodes:
                    node_id = n["id"]
                    
                    # Skip if this node was recently removed by user (only applies to stale re-sends)
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
                    # Ensure context nodes are highlighted immediately
                    active_context_ids = [n['id'] for n in st.session_state.context_nodes]
                    st.session_state.highlight_nodes = list(set(st.session_state.highlight_nodes + active_context_ids))
                    st.rerun()

with col_chat:
    # --- Callback functions for context management (defined outside container) ---
    def remove_node_callback(node_id):
        """Remove a specific node from context."""
        st.session_state.context_nodes = [n for n in st.session_state.context_nodes if n['id'] != node_id]
        
        # Always clear the processed signature so user can re-add the same node
        st.session_state.last_processed_context_update = None
        
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
        # Clear the processed update signature so user can re-add the same nodes later
        st.session_state.last_processed_context_update = None
    
    # Header row with Chat title and Context dropdown
    header_col1, header_col2 = st.columns([1, 1], vertical_alignment="bottom")
    with header_col1:
        st.subheader("Chat")
    with header_col2:
        # Context indicator and popover in the header
        if st.session_state.context_nodes:
            context_count = len(st.session_state.context_nodes)
            with st.popover(f"📚 Context ({context_count})", use_container_width=True):
                st.markdown("**Active Context**")
                st.markdown("---")
                for idx, node in enumerate(st.session_state.context_nodes):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{node['label']}**")
                        if node.get('files'):
                            for f in node['files']:
                                st.caption(f"• {f}")
                        else:
                            st.caption("(No files)")
                    with col2:
                        st.button(
                            "❌",
                            key=f"remove_node_{node['id']}",
                            help=f"Remove {node['label']}",
                            on_click=remove_node_callback,
                            args=(node['id'],)
                        )
                    if idx < len(st.session_state.context_nodes) - 1:
                        st.markdown("---")
                
                st.markdown("")
                st.button(
                    "🗑️ Clear All",
                    key="clear_all_ctx_btn",
                    on_click=clear_all_context_callback,
                    use_container_width=True
                )
        else:
            st.caption("📚 No context selected")
    
    # Create a scrollable container for the chat area
    with st.container(height=620):
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
        
        # Show processing indicator inside the scrollable container
        if st.session_state.is_processing:
            with st.chat_message("assistant"):
                st.write("🔄 Analyzing...")

    # Chat input stays outside the scrollable container (fixed at bottom)
    if prompt := st.chat_input("Ask about the files..."):
        # Save user message and set processing flag, then rerun to show the message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.is_processing = True
        st.session_state.pending_prompt = prompt  # Store for processing after rerun
        st.rerun()
    
    # Process pending prompt (after rerun, so user message is visible)
    if st.session_state.is_processing and st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None  # Clear to avoid reprocessing
        
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
                
                # Get expected path segment based on industry
                expected_path_segment = get_expected_path_segment(node_id)
                
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
            # Search within the selected industry only
            industry_filter = "Restaurant_Franchise" if st.session_state.selected_industry == "fnb" else "Legal_Firm"
            relevant_docs = search_files(prompt, st.session_state.records, k=50, industry_filter=industry_filter)

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
            new_highlights = extract_node_ids_from_paths(
                [d['path'] for d in high_relevance_docs], 
                industry=st.session_state.selected_industry
            )
            st.session_state.highlight_nodes = new_highlights
        else:
            st.session_state.highlight_nodes = []

        # AI Response - process and save, then rerun to display inside container
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
            
            # Save response to session state and clear processing flag
            st.session_state.messages.append({
                "role": "assistant", 
                "content": answer,
                "relevant_docs": high_relevance_docs
            })
            st.session_state.is_processing = False
            
            # Rerun to display messages inside the scrollable container
            st.rerun()
            
        except Exception as e:
            st.session_state.is_processing = False
            st.error(f"Error: {e}")
