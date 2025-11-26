# Architecture & Technical Guide

## Architecture Overview

### Frontend
`diagram-prototype/src/App.tsx` powers the embedded board using React Flow. It listens for props from Streamlit, overlays highlight styling, and exposes controls for snapping, themes, edge markers, and the **Add to Context** action.

**Key Features:**
- **Editable Nodes**: Custom `EditableNode.tsx` supports inline renaming, resizing, and rich visual feedback (highlights/selection).
- **State Management**: Selection state stays local to React Flow; significant actions (like **Add to Context**) post events back to Streamlit via `Streamlit.setComponentValue`.
- **Integration**: `_contextUpdate` events bridge the React frontend with the Python backend.
- **Build Artifacts**: The frontend is built into `diagram-prototype/dist/`, which is served by the Streamlit component.

**State Synchronization Challenge:**
The React component maintains its own selection state, which can persist across Streamlit reruns. This creates a "two brains" problem where the frontend and backend can disagree. The backend uses deduplication flags (`last_processed_context_update`) and blocklists (`recently_removed_ids`) to prevent stale React events from re-adding cleared nodes.

### Backend
`app.py` is the Streamlit entrypoint. It seeds the logical tree, converts it to React Flow nodes/edges, renders the custom component, and handles context/chat events.

**Session State Tracks:**
- Chat history (`messages`)
- Active context nodes (`context_nodes`)
- Highlighted nodes from search results (`highlight_nodes`)
- Cached file index (`records`)
- Selected OpenAI model
- Sync control flags (`ignore_context_updates`, `recently_removed_ids`, `last_processed_context_update`)

**Core Logic:**
- `convert_to_react_flow_nodes_and_edges()`: Transforms the logical tree into visual nodes with fixed layout coordinates.
- `map_node_to_files()`: Derives filesystem paths from node IDs (e.g., `west_accounting` → `sample_data/West_Group/Accounting`).
- Chat requests: If context nodes are selected, use files from those nodes directly; otherwise, run `search_files` -> Highlight matching nodes -> Call OpenAI.

### Data Layer
`sample_data/` mirrors the board structure. Each `*_Group` directory contains department folders with canonical documents (PDFs, CSVs, XLSX, etc.).

`document_search.py` provides:
- `scan_dummy_data`: Indexes the filesystem (supports .txt, .md, .csv, and .pdf via pypdf).
- `search_files`: Performs weighted keyword search with location/category boosting.
- `extract_node_ids_from_paths`: Maps file hits back to visual node IDs for highlighting.

## Key Files & Directories
- `app.py`: Streamlit application main file.
- `streamlit_miro_component/`: Python wrapper that serves the built assets from `diagram-prototype/dist/`.
- `diagram-prototype/`: Vite + React Flow project (source for the board component).
- `sample_data/`: Synthetic documents for demo purposes.
- `document_search.py`: Search logic and file system scanning.
- `.streamlit/secrets.toml`: Local secrets configuration (not tracked).

## End-to-End Flow
1. **Boot**: `scan_dummy_data` indexes `sample_data/`.
2. **Render**: `app.py` sends initial node/edge data to the React component.
3. **Interact**: User interacts with the board (select, resize, edit).
4. **Context**: User clicks **Add to Context** -> React emits `_contextUpdate` -> Streamlit updates session state.
5. **Chat**: User asks a question -> If context nodes exist, use their files directly; otherwise search all files -> Updates chat & highlights board nodes.
6. **Response**: AI generates answer based on retrieved excerpts.

## Extending the Project
- **Board Experience**: Customize `EditableNode.tsx` for new visual types or interaction modes.
- **Data Mappings**: Enhance `map_node_to_files` for dynamic or database-backed file associations.
- **RAG Pipeline**: Swap heuristic search in `document_search.py` for a Vector DB (Chroma/Pinecone) and embeddings.
- **Persistence**: Implement state sync to save board edits back to a backend database.

