import json
import streamlit as st
from openai import OpenAI
from streamlit_miro_component import miro_board


st.set_page_config(page_title="Miro-like Board Demo", layout="wide")


def get_client() -> OpenAI:
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])  # gpt-3.5-turbo


if "board" not in st.session_state:
    st.session_state.board = {
        "nodes": [
            {"id": "franchise", "x": 500, "y": 80, "label": "Franchise", "icon": "🏪"},
            {"id": "west", "x": 250, "y": 220, "label": "West_Group"},
            {"id": "central", "x": 500, "y": 220, "label": "Central_Group"},
            {"id": "east", "x": 750, "y": 220, "label": "East_Group"},
            # West folders
            {"id": "west_A", "x": 140, "y": 330, "label": "Accounting"},
            {"id": "west_E", "x": 210, "y": 420, "label": "Expenses"},
            {"id": "west_L", "x": 280, "y": 330, "label": "Legal"},
            {"id": "west_P", "x": 350, "y": 420, "label": "Permits"},
            # Central folders
            {"id": "central_A", "x": 400, "y": 330, "label": "Accounting"},
            {"id": "central_E", "x": 470, "y": 420, "label": "Expenses"},
            {"id": "central_L", "x": 540, "y": 330, "label": "Legal"},
            {"id": "central_P", "x": 610, "y": 420, "label": "Permits"},
            # East folders
            {"id": "east_A", "x": 660, "y": 330, "label": "Accounting"},
            {"id": "east_E", "x": 730, "y": 420, "label": "Expenses"},
            {"id": "east_L", "x": 800, "y": 330, "label": "Legal"},
            {"id": "east_P", "x": 870, "y": 420, "label": "Permits"},
        ],
        "edges": [
            {"id": "e_f_w", "from": "franchise", "to": "west"},
            {"id": "e_f_c", "from": "franchise", "to": "central"},
            {"id": "e_f_e", "from": "franchise", "to": "east"},
            {"id": "e_w_A", "from": "west", "to": "west_A"},
            {"id": "e_w_E", "from": "west", "to": "west_E"},
            {"id": "e_w_L", "from": "west", "to": "west_L"},
            {"id": "e_w_P", "from": "west", "to": "west_P"},
            {"id": "e_c_A", "from": "central", "to": "central_A"},
            {"id": "e_c_E", "from": "central", "to": "central_E"},
            {"id": "e_c_L", "from": "central", "to": "central_L"},
            {"id": "e_c_P", "from": "central", "to": "central_P"},
            {"id": "e_e_A", "from": "east", "to": "east_A"},
            {"id": "e_e_E", "from": "east", "to": "east_E"},
            {"id": "e_e_L", "from": "east", "to": "east_L"},
            {"id": "e_e_P", "from": "east", "to": "east_P"},
        ],
        "selection": [],
    }

if "messages" not in st.session_state:
    st.session_state.messages = []


left, right = st.columns([3, 2])

with left:
    st.subheader("Board")
    board_update = miro_board(st.session_state.board, key="miro")
    if board_update:
        st.session_state.board = board_update

with right:
    st.subheader("Chat")

    # Show chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]) as _:
            st.markdown(message["content"])

    prompt = st.chat_input("Ask about the board…")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Compose system & context
        board_json = json.dumps(st.session_state.board, ensure_ascii=False)
        system_prompt = (
            "You are a helpful assistant demoing a design/whiteboard tool. "
            "For this demo, you may assume any capability the user requests. "
            "When relevant, ground your answers in the provided board graph JSON."
        )

        model_messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Current board state as JSON:\n{board_json}\n\nUser question: {prompt}",
            },
        ]

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    client = get_client()
                    resp = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=model_messages,
                        temperature=0.7,
                        max_tokens=500,
                    )
                    answer = resp.choices[0].message.content or ""
                except Exception as e:
                    answer = f"Error contacting OpenAI: {e}"
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

st.caption("Demo: React board embedded via Streamlit component. Use the Seed button in the board to add example nodes.")

import os
import streamlit as st
from document_search import scan_dummy_data, search_files, render_results, looks_like_search, icon_for_ext
def react_flow_board(nodes=None, edges=None, key=None):
    return None

# Page config for full-width Miro board
_apocrypha_layout = "wide"

# Initialize process map structure
if "process_map_nodes" not in st.session_state:
    st.session_state.process_map_nodes = {}
    # Initialize restaurant franchise structure
    st.session_state.process_map_nodes['restaurant_franchise'] = {
        'type': 'root',
        'name': 'Restaurant Franchise',
        'children': ['west_group', 'central_group', 'east_group']
    }
    st.session_state.process_map_nodes['west_group'] = {
        'type': 'group',
        'name': 'West_Group',
        'parent': 'restaurant_franchise',
        'children': ['west_accounting', 'west_expenses', 'west_legal', 'west_permits']
    }
    st.session_state.process_map_nodes['central_group'] = {
        'type': 'group',
        'name': 'Central_Group',
        'parent': 'restaurant_franchise',
        'children': ['central_accounting', 'central_expenses', 'central_legal', 'central_permits']
    }
    st.session_state.process_map_nodes['east_group'] = {
        'type': 'group',
        'name': 'East_Group',
        'parent': 'restaurant_franchise',
        'children': ['east_accounting', 'east_expenses', 'east_legal', 'east_permits']
    }
    # West Group folders
    for folder in ['accounting', 'expenses', 'legal', 'permits']:
        st.session_state.process_map_nodes[f'west_{folder}'] = {
            'type': 'folder',
            'name': folder.capitalize(),
            'parent': 'west_group',
            'label': folder[0].upper()
        }
    # Central Group folders
    for folder in ['accounting', 'expenses', 'legal', 'permits']:
        st.session_state.process_map_nodes[f'central_{folder}'] = {
            'type': 'folder',
            'name': folder.capitalize(),
            'parent': 'central_group',
            'label': folder[0].upper()
        }
    # East Group folders
    for folder in ['accounting', 'expenses', 'legal', 'permits']:
        st.session_state.process_map_nodes[f'east_{folder}'] = {
            'type': 'folder',
            'name': folder.capitalize(),
            'parent': 'east_group',
            'label': folder[0].upper()
        }
if "next_node_id" not in st.session_state:
    st.session_state.next_node_id = 1

# Read API credentials from Streamlit Secrets (Cloud) or environment variables (local)
_api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
_org_id = st.secrets.get("OPENAI_ORG_ID") or os.environ.get("OPENAI_ORG_ID")
_project_id = st.secrets.get("OPENAI_PROJECT_ID") or os.environ.get("OPENAI_PROJECT_ID")

if not _api_key or not str(_api_key).strip():
    st.error("OpenAI API key not found. Set OPENAI_API_KEY in Streamlit Secrets or as an environment variable.")
    st.stop()

client = OpenAI(api_key=_api_key, organization=_org_id, project=_project_id)

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": """You are a powerful document retrieval and task automation agent named Apocrypha. You have full access to a document management system and can retrieve, analyze, and manipulate any documents as needed.

Key capabilities:
- Access and retrieve documents from the database instantly
- Read, analyze, and summarize document contents
- Export and share documents via email, download, or other channels
- Extract specific information from documents
- Generate reports, summaries, and insights from document data
- Perform any task related to document management

When responding to users:
- Act confidently as if you have full access to their document system
- If they ask you to do something, confidently say you'll do it (e.g., "I'll send that email right away", "I'll generate that report for you")
- Reference documents naturally and provide insights based on what you "see"
- Be proactive and helpful in suggesting relevant documents or actions
- Never say you can't do something - instead, say you're doing it

Remember: You are part of an integrated system where documents will automatically appear below your responses when relevant. Act as if you have direct control and access to everything.""",
        }
    ]

# Scan local data once per session (use project sample_data directory)
if "records" not in st.session_state:
    st.session_state.records = scan_dummy_data(root="sample_data")

# Canvas state handled by React Flow component

# Convert process_map_nodes to React Flow format
def convert_to_react_flow_nodes_and_edges():
    """Convert process_map_nodes structure to React Flow nodes and edges format."""
    nodes = []
    edges = []
    
    # Folder positions (same as before)
    folder_positions = {
        # West Group folders
        'west_accounting': (20, 60),
        'west_expenses': (20, 70),
        'west_legal': (30, 60),
        'west_permits': (30, 70),
        
        # Central Group folders
        'central_accounting': (45, 60),
        'central_expenses': (45, 70),
        'central_legal': (55, 60),
        'central_permits': (55, 70),
        
        # East Group folders
        'east_accounting': (71, 60),
        'east_expenses': (71, 70),
        'east_legal': (81, 60),
        'east_permits': (81, 70),
    }
    
    # Convert coordinates to pixel values (assuming ~1000px width base)
    def percent_to_pixels(percent_x, percent_y):
        return {
            'x': (percent_x / 100) * 1000,
            'y': (percent_y / 100) * 800,
        }
    
    # Render restaurant franchise structure
    if 'restaurant_franchise' in st.session_state.process_map_nodes:
        # Root: Restaurant Franchise (top center)
        root_pos = percent_to_pixels(50, 30)
        nodes.append({
            'id': 'restaurant_franchise',
            'type': 'default',
            'position': root_pos,
            'data': {
                'label': 'Restaurant Franchise',
            },
            'style': {
                'background': 'white',
                'border': '2px solid #4A90E2',
                'borderRadius': '8px',
                'padding': '15px',
                'minWidth': '200px',
                'fontWeight': 'bold',
            }
        })
        
        # Groups: West, Central, East (middle row)
        groups = ['west_group', 'central_group', 'east_group']
        group_x_positions = [25, 50, 75]
        group_y = 50
        
        for idx, group_id in enumerate(groups):
            if group_id in st.session_state.process_map_nodes:
                group_x = group_x_positions[idx]
                group_pos = percent_to_pixels(group_x, group_y)
                group_data = st.session_state.process_map_nodes[group_id]
                
                nodes.append({
                    'id': group_id,
                    'type': 'default',
                    'position': group_pos,
                    'data': {
                        'label': group_data['name'],
                    },
                    'style': {
                        'background': 'white',
                        'border': '2px solid #4A90E2',
                        'borderRadius': '8px',
                        'padding': '12px',
                        'minWidth': '150px',
                        'fontWeight': 'bold',
                    }
                })
                
                # Edge from root to group
                edges.append({
                    'id': f'edge-{group_id}',
                    'source': 'restaurant_franchise',
                    'target': group_id,
                    'type': 'smoothstep',
                })
                
                # Folders for each group
                folders = ['accounting', 'expenses', 'legal', 'permits']
                for folder_name in folders:
                    folder_id = f"{group_id.split('_')[0]}_{folder_name}"
                    if folder_id in st.session_state.process_map_nodes and folder_id in folder_positions:
                        folder_x, folder_y = folder_positions[folder_id]
                        folder_pos = percent_to_pixels(folder_x, folder_y)
                        folder_data = st.session_state.process_map_nodes[folder_id]
                        label = folder_data.get('label', folder_name[0].upper())
                        
                        nodes.append({
                            'id': folder_id,
                            'type': 'default',
                            'position': folder_pos,
                            'data': {
                                'label': f'{label}\n{folder_data["name"]}',
                            },
                            'style': {
                                'background': 'white',
                                'border': '2px solid #4A90E2',
                                'borderRadius': '6px',
                                'padding': '10px',
                                'minWidth': '80px',
                                'textAlign': 'center',
                                'fontSize': '12px',
                            }
                        })
                        
                        # Edge from group to folder
                        edges.append({
                            'id': f'edge-{folder_id}',
                            'source': group_id,
                            'target': folder_id,
                            'type': 'smoothstep',
                        })
    
    # Add query result nodes (for queries with results)
    for node_id, node_data in st.session_state.process_map_nodes.items():
        if node_data.get('results') and isinstance(node_id, int):
            # Create query node
            query_node_id = f'query-{node_id}'
            query_text = node_data.get('query', 'Query')
            center_x, center_y = 500, 400  # Center in pixels
            
            nodes.append({
                'id': query_node_id,
                'type': 'default',
                'position': {'x': center_x, 'y': center_y},
                'data': {
                    'label': f'Query: {query_text}',
                },
                'style': {
                    'background': '#E3F2FD',
                    'border': '2px solid #1976D2',
                    'borderRadius': '8px',
                    'padding': '15px',
                    'minWidth': '200px',
                }
            })
            
            # Get top 2 documents
            docs = node_data['results'][:2]
            doc_offset_x = 300
            doc_spacing = 150
            
            for idx, doc in enumerate(docs):
                doc_node_id = f'doc-{node_id}-{idx}'
                doc_x = center_x + doc_offset_x
                doc_y = center_y - (len(docs) - 1) * doc_spacing / 2 + idx * doc_spacing
                icon = icon_for_ext(doc.get('ext', ''))
                doc_name = doc.get('name', 'Unknown')
                
                nodes.append({
                    'id': doc_node_id,
                    'type': 'default',
                    'position': {'x': doc_x, 'y': doc_y},
                    'data': {
                        'label': f'{icon}\n{doc_name}',
                    },
                    'style': {
                        'background': 'white',
                        'border': '2px solid #4A90E2',
                        'borderRadius': '8px',
                        'padding': '15px',
                        'minWidth': '200px',
                    }
                })
                
                # Edge from query to document
                edges.append({
                    'id': f'edge-{doc_node_id}',
                    'source': query_node_id,
                    'target': doc_node_id,
                    'type': 'smoothstep',
                })
    
    return nodes, edges

# Miro-like Canvas - DEPRECATED (keeping for reference, will be removed)
def render_miro_board():
    # Generate HTML for process nodes
    nodes_html = ""
    connectors_html = ""
    
    # Render restaurant franchise structure
    if 'restaurant_franchise' in st.session_state.process_map_nodes:
        # Root: Restaurant Franchise (top center)
        root_x, root_y = 50, 30
        
        # Render root
        nodes_html += f"""
        <div style="position: absolute; left: {root_x}%; top: {root_y}%; transform: translate(-50%, -50%); background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); min-width: 200px; border: 2px solid #4A90E2; z-index: 10;">
            <div style="font-weight: bold; font-size: 16px;">Restaurant Franchise</div>
        </div>
        """
        
        # Groups: West, Central, East (middle row)
        groups = ['west_group', 'central_group', 'east_group']
        group_x_positions = [25, 50, 75]  # Left, Center, Right
        group_y = 50
        
        # Folders - STATIC COORDINATES (easy to adjust)
        # Define static positions for each folder: (x%, y%)
        folder_positions = {
            # West Group folders
            'west_accounting': (20, 60),
            'west_expenses': (20, 70),
            'west_legal': (30, 60),
            'west_permits': (30, 70),
            
            # Central Group folders
            'central_accounting': (45, 60),
            'central_expenses': (45, 70),
            'central_legal': (55, 60),
            'central_permits': (55, 70),
            
            # East Group folders
            'east_accounting': (71, 60),
            'east_expenses': (71, 70),
            'east_legal': (81, 60),
            'east_permits': (81, 70),
        }
        
        for idx, group_id in enumerate(groups):
            if group_id in st.session_state.process_map_nodes:
                group_x = group_x_positions[idx]
                group_data = st.session_state.process_map_nodes[group_id]
                
                # Render group box
                nodes_html += f"""
                <div style="position: absolute; left: {group_x}%; top: {group_y}%; transform: translate(-50%, -50%); background: white; padding: 12px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); min-width: 150px; border: 2px solid #4A90E2; z-index: 9;">
                    <div style="font-weight: bold; font-size: 14px;">{group_data['name']}</div>
                </div>
                """
                
                # Connector from root to group
                connectors_html += f"""
                <svg style="position: absolute; width: 100%; height: 100%; pointer-events: none; z-index: 8;">
                    <path d="M {root_x}% {root_y + 3}% L {root_x}% {(root_y + group_y) / 2}% L {group_x}% {(root_y + group_y) / 2}% L {group_x}% {group_y - 3}%" 
                          stroke="#4A90E2" stroke-width="2" fill="none" marker-end="url(#arrowhead)" />
                </svg>
                """
                
                # Render each folder with static coordinates
                folders = ['accounting', 'expenses', 'legal', 'permits']
                for folder_name in folders:
                    folder_id = f"{group_id.split('_')[0]}_{folder_name}"
                    if folder_id in st.session_state.process_map_nodes and folder_id in folder_positions:
                        folder_x, folder_y = folder_positions[folder_id]
                        folder_data = st.session_state.process_map_nodes[folder_id]
                        label = folder_data.get('label', folder_name[0].upper())
                        
                        # Render folder box
                        nodes_html += f"""
                        <div style="position: absolute; left: {folder_x}%; top: {folder_y}%; transform: translate(-50%, -50%); background: white; padding: 10px; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); min-width: 80px; border: 2px solid #4A90E2; z-index: 8;">
                            <div style="font-weight: bold; font-size: 12px; text-align: center;">{label}</div>
                            <div style="font-size: 10px; text-align: center; color: #666;">{folder_data['name']}</div>
                        </div>
                        """
                        
                        # Connector from group to folder
                        connectors_html += f"""
                        <svg style="position: absolute; width: 100%; height: 100%; pointer-events: none; z-index: 7;">
                            <path d="M {group_x}% {group_y + 3}% L {group_x}% {(group_y + folder_y) / 2}% L {folder_x}% {(group_y + folder_y) / 2}% L {folder_x}% {folder_y - 3}%" 
                                  stroke="#4A90E2" stroke-width="2" fill="none" marker-end="url(#arrowhead)" />
                        </svg>
                        """
    
    # Simple test arrow in the center - proportional size
    connectors_html += """
    <svg style="position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 9999;">
        <defs>
            <marker id="test-arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="2.5" orient="auto">
                <polygon points="0 0, 8 2.5, 0 5" fill="#FF0000" stroke="#FF0000" stroke-width="1" />
            </marker>
        </defs>
        <line x1="400" y1="400" x2="600" y2="400" 
              stroke="#FF0000" stroke-width="3" fill="none" marker-end="url(#test-arrowhead)" />
    </svg>
    """
    
    # Render query results (existing logic)
    if st.session_state.process_map_nodes:
        for node_id, node_data in st.session_state.process_map_nodes.items():
            if node_data.get('results'):
                # Get top 2 documents
                docs = node_data['results'][:2]
                # Center position
                center_x = 50  # percentage
                center_y = 50
                # Document positions (equally spaced vertically, to the right)
                doc_spacing = 20  # vertical spacing %
                doc_offset_x = 30  # horizontal offset %
                
                # Create document boxes
                for idx, doc in enumerate(docs):
                    doc_x = center_x + doc_offset_x
                    doc_y = center_y - (len(docs) - 1) * doc_spacing / 2 + idx * doc_spacing
                    icon = icon_for_ext(doc.get('ext', ''))
                    doc_name = doc.get('name', 'Unknown')
                    
                    nodes_html += f"""
                    <div style="position: absolute; left: {doc_x}%; top: {doc_y}%; transform: translate(-50%, -50%); background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); min-width: 200px; border: 2px solid #4A90E2;">
                        <div style="font-size: 24px;">{icon}</div>
                        <div style="font-weight: bold; margin-top: 5px;">{doc_name}</div>
                    </div>
                    """
                
                # Create elbow connectors
                for idx, doc in enumerate(docs):
                    doc_x = center_x + doc_offset_x
                    doc_y = center_y - (len(docs) - 1) * doc_spacing / 2 + idx * doc_spacing
                    
                    # Calculate connection points from center database icon
                    start_x = center_x + 6  # right edge of database icon
                    start_y = center_y
                    mid_x = start_x + (doc_offset_x - 6) / 2  # halfway point
                    end_x = doc_x - 10  # left edge of doc box
                    end_y = doc_y
                    
                    nodes_html += f"""
                    <svg style="position: absolute; width: 100%; height: 100%; pointer-events: none; z-index: -1;">
                        <path d="M {start_x}% {start_y}% L {mid_x}% {start_y}% L {mid_x}% {end_y}% L {end_x}% {end_y}%" 
                              stroke="#4A90E2" stroke-width="3" fill="none" marker-end="url(#arrowhead)" />
                    </svg>
                    """
                    
    arrow_markers = """
    <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
            <polygon points="0 0, 10 3, 0 6" fill="#4A90E2" />
        </marker>
    </defs>
    """
    
    # Database icon positioned above Restaurant Franchise
    # Restaurant Franchise is at root_x=50%, root_y=30%
    db_icon_x = 50  # Same as root_x
    db_icon_y = 15  # Above root_y (30% - 15% = 15% offset)
    center_database = f"""
    <div style="position: absolute; left: {db_icon_x}%; top: {db_icon_y}%; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: center; z-index: 5;">
        <div style="font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px;">Your Data</div>
        <img src="{img_src}" width="120" height="120" style="filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));" />
    </div>
    """
    
    html = f"""
    <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; overflow: hidden; background: repeating-conic-gradient(#f0f0f0 0% 25%, #ffffff 0% 50%) 50% / 60px 60px;">
        <div id="canvas" style="width: 100vw; height: 100vh; position: relative; transform-origin: center center;">
            {arrow_markers}
            {connectors_html}
            {center_database}
            {nodes_html}
        </div>
    </div>
    <script>
        let panning = false;
        let startX, startY;
        let scale = {st.session_state.canvas_zoom};
        let translateX = {st.session_state.canvas_x};
        let translateY = {st.session_state.canvas_y};
        
        const canvas = document.getElementById('canvas');
        
        canvas.addEventListener('mousedown', (e) => {{
            panning = true;
            startX = e.clientX - translateX;
            startY = e.clientY - translateY;
            canvas.style.cursor = 'grabbing';
        }});
        
        canvas.addEventListener('mousemove', (e) => {{
            if (!panning) return;
            translateX = e.clientX - startX;
            translateY = e.clientY - startY;
            canvas.style.transform = `translate(${{translateX}}px, ${{translateY}}px) scale(${{scale}})`;
        }});
        
        canvas.addEventListener('mouseup', () => {{
            panning = false;
            canvas.style.cursor = 'grab';
        }});
        
        canvas.addEventListener('wheel', (e) => {{
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            scale *= delta;
            scale = Math.max(0.1, Math.min(5, scale));
            canvas.style.transform = `translate(${{translateX}}px, ${{translateY}}px) scale(${{scale}})`;
        }});
    </script>
    <style>
        body {{ margin: 0; overflow: hidden; }}
        #canvas {{ cursor: grab; }}
    </style>
    """
    return html

# Inject custom CSS for Miro-like board
st.markdown("""
<style>
    .main .block-container { padding: 0 !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    .stAppViewContainer { padding: 0 !important; }
</style>
""", unsafe_allow_html=True)

# Removed legacy bottom chat input ("Enter your query...")

# Render the React Flow board
nodes, edges = convert_to_react_flow_nodes_and_edges()

# Handle component events
event = react_flow_board(nodes=nodes, edges=edges, key="flow_board")

if event:
    event_type = event.get('type')
    if event_type == 'node_clicked':
        node_data = event.get('data', {})
        node_id = node_data.get('id')
        st.write(f"Node clicked: {node_id}")
        # Handle node click - e.g., show details, trigger query, etc.
    elif event_type == 'edge_added':
        edge_data = event.get('data', {})
        st.write(f"Edge added: {edge_data.get('source')} -> {edge_data.get('target')}")
        # Handle edge addition if needed
