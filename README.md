# Apocrypha Diagram MVP

Apocrypha Diagram MVP is a Streamlit + React Flow prototype that mirrors a prospect’s folder hierarchy, lets facilitators “attach” representative sample data, and walks through a lightweight RAG-style chat. During a session you sketch a franchise → region → department → document tree, add folders to the active context, and run questions that highlight matching branches on the board. The code currently lives in the `punnkrit/Apocrypha_Miro` fork so collaborators can pull from or PR against it directly.

## Typical User Flow
1. Launch Streamlit to render the left/right split view.
2. Draw or tweak the board in the React Flow canvas (pan/zoom, add nodes, toggle grid).
3. Select one or more nodes and click **Add to Context** – Streamlit maps those nodes to `sample_data/` folders, stores the files, and logs a system message.
4. Inspect the **Active Context** panel to confirm what’s in play; clear/reset as needed.
5. Ask a question in chat. The request runs through `document_search.py`, filters by context folders, and returns the top hits.
6. Receive an answer (optionally augmented by OpenAI) along with document references and highlighted nodes on the diagram.

## Architecture
### Frontend
`diagram-prototype/src/App.tsx` powers the embedded board. It listens for props from Streamlit, overlays highlight styling, and exposes controls for snapping, themes, edge markers, and the **Add to Context** action.

```48:120:diagram-prototype/src/App.tsx
const onRender = (event: Event) => {
  const customEvent = event as CustomEvent<RenderData>;
  const args = customEvent.detail.args;

  if (args.nodes && Array.isArray(args.nodes)) {
     const highlights = args.highlight_nodes || [];
     setNodes((currentNodes) => {
         const newNodes = args.nodes.map((serverNode: any) => {
             const existing = currentNodes.find(n => n.id === serverNode.id);
             const isHighlighted = highlights.includes(serverNode.id);
             let style = { ...serverNode.style };
             if (isHighlighted) {
                 style.border = '3px solid #ff9900';
                 style.boxShadow = '0 0 15px rgba(255, 153, 0, 0.6)';
             }
             return {
                 ...serverNode,
                 position: existing ? existing.position : serverNode.position,
                 style,
                 data: { ...serverNode.data }
             };
         });
         if (currentNodes.length === 0) return newNodes;
         return newNodes;
     });
  }
```

Selection state stays local to React Flow; when **Add to Context** fires it posts `_contextUpdate` back through `Streamlit.setComponentValue`, which Streamlit picks up as `component_state`.

```181:244:diagram-prototype/src/App.tsx
const handleAddToContext = () => {
    if (selectedNodes.length === 0) return;

    const contextUpdate = {
        type: 'add_to_context',
        nodes: selectedNodes.map(n => ({ id: n.id, label: n.data.label })),
    };

    Streamlit.setComponentValue({
        _contextUpdate: contextUpdate,
    });
};
```

`EditableNode.tsx` is available for inline renaming/resizing if you prefer custom node types instead of React Flow defaults.

### Backend
`app.py` seeds the logical tree, converts it to React Flow nodes/edges, renders `miro_board`, and handles context/chat events. Session state tracks chat history, context nodes, highlight IDs, the cached file index, and the selected OpenAI model.

```184:236:app.py
with col_board:
    rf_nodes, rf_edges = convert_to_react_flow_nodes_and_edges()
    highlights = st.session_state.highlight_nodes
    component_state = miro_board(nodes=rf_nodes, edges=rf_edges, highlight_nodes=highlights, key="main_board")

    if component_state and "_contextUpdate" in component_state:
        update = component_state["_contextUpdate"]
        if update.get("type") == "add_to_context":
            new_nodes = update.get("nodes", [])
            for n in new_nodes:
                if not any(existing["id"] == n["id"] for existing in st.session_state.context_nodes):
                    files = map_node_to_files(n["id"])
                    node_with_files = {**n, "files": files}
                    st.session_state.context_nodes.append(node_with_files)
                    st.session_state.messages.append({
                        "role": "system",
                        "content": f"📂 Added {n['label']} to context ({len(files)} files found)."
                    })
            st.rerun()
```

`map_node_to_files` derives filesystem paths from node IDs (e.g., `west_accounting` → `sample_data/West_Group/Accounting`). Chat requests append to `st.session_state.messages`, run `search_files` against the pre-built record index, highlight the nodes representing matching documents, and optionally call OpenAI using credentials from `.streamlit/secrets.toml` or `OPENAI_API_KEY`.

### Data Layer
`sample_data/` mirrors the board: each `*_Group` directory contains Accounting, Expenses, Legal, and Permits folders with canonical documents (PDFs, CSVs, XLSX, etc.), plus a few root-level assets for demos. `document_search.py` walks the tree once, caches metadata, and exposes helpers for keyword search, icon rendering, highlight inference, and query heuristics (location/category detection).

## Key Files & Directories
- `app.py` – Streamlit entrypoint; manages session state, renders the component, handles context events, and runs the chat/RAG loop.
- `streamlit_miro_component/` – Wraps the React build artifact (`diagram-prototype/dist`) or dev server URL and exposes `miro_board`.
- `diagram-prototype/` – Vite + React Flow project (board, editable node, styles, build tooling).
- `sample_data/` – Synthetic documents organized by franchise group and department.
- `document_search.py` – Scans sample data, performs heuristic search, renders hits, and maps file paths back to node IDs.
- `.streamlit/secrets.toml` – Local secrets (OpenAI key, org info). Not tracked.
- `requirements.txt` – Python dependencies (Streamlit + OpenAI).
- `debug_openai*.py` – Helper scripts for troubleshooting OpenAI connectivity.

## End-to-End Flow
1. **Python boot**: `scan_dummy_data` indexes `sample_data/`; the franchise tree is cached under `st.session_state.process_map_nodes`.
2. **Render board**: `convert_to_react_flow_nodes_and_edges` constructs positioned nodes/edges and passes them into `miro_board`, along with any highlight IDs from prior searches.
3. **User interaction**: React Flow handles selection/editing. When **Add to Context** fires, it emits node IDs + labels back to Streamlit.
4. **Context enrichment**: Streamlit receives `_contextUpdate`, deduplicates entries, resolves filesystem files, updates the context list, and logs a system message.
5. **Chat + RAG**: Prompts feed into `search_files`, which filters by context folders (falling back to the full dataset). Matching docs are shown inline; paths convert to board node IDs via `extract_node_ids_from_paths` for highlights.
6. **AI response**: If OpenAI is configured, the assistant call includes short document excerpts; otherwise, you can stub or log the search results.

## Local Development
### Python / Streamlit
```bash
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` with:
```toml
OPENAI_API_KEY = "sk-..."
```

Run the app:
```bash
streamlit run app.py
```

### React Diagram Component
```bash
cd diagram-prototype
npm install
npm run dev   # set MIRO_DEV_URL=http://localhost:5173 before launching Streamlit
npm run build # emits dist/ for production use
```

Setting `MIRO_DEV_URL` makes Streamlit load the live dev server; unsetting it falls back to the built `dist/`.

## Extending the Project
- **Board experience**: Modify node styles or hierarchy in `convert_to_react_flow_nodes_and_edges`, or switch Python nodes to `editableNode` to unlock inline editing.
- **Custom events**: Extend `_contextUpdate` (remove-from-context, metadata edits) and update the Streamlit handler accordingly.
- **Data mappings**: Expand `map_node_to_files` to support deeper or dynamic structures, or persist per-node path metadata.
- **RAG pipeline**: Replace `search_files` with embeddings + vector DB calls, wiring outputs back into the chat similarly.
- **Context/UI**: Add document previews, analytics, or persist context selections across sessions.

## Implementation Notes / Potential Improvements
- Node IDs currently encode `<region>_<category>`; real deployments need explicit mapping to arbitrary customer folders.
- `extract_node_ids_from_paths` distinguishes departments via a single letter (A/E/L/P); new departments require logic updates.
- Context, highlights, and chat history only live in Streamlit session state—refreshing clears them.
- The frontend doesn’t stream node edits back to Python yet; add a periodic state sync if you need parity.
- Secrets should ultimately come from environment variables or a secure store for deployments.

