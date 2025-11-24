# Apocrypha Diagram MVP

Apocrypha Diagram MVP is a Streamlit + React Flow prototype that visualizes a prospect’s folder hierarchy, enables interactive data context selection, and provides a lightweight RAG-style chat interface.

Users can sketch a franchise structure (Franchise → Region → Department), select nodes to "add to context," and then ask questions. The system searches relevant files and highlights matching branches on the diagram.

## Features
- **Interactive Diagram**: React Flow powered board with draggable, resizable, and editable nodes.
- **Context-Aware Chat**: Filter search results based on selected diagram nodes.
- **Visual Feedback**: Real-time highlighting of nodes that contain relevant documents.
- **Document Intelligence**: Scans and indexes local sample data to answer user queries.

## Typical User Flow
1. **Launch**: Open the Streamlit app to see the split view (Board + Chat).
2. **Edit**: Draw or tweak the board (pan/zoom, add/edit nodes, toggle grid).
3. **Select**: Pick nodes and click **Add to Context**.
4. **Verify**: Check the **Active Context** panel.
5. **Ask**: Chat with the system. "What is the total expense for the West Group?"
6. **Visualize**: See the answer and watch relevant nodes light up on the board.

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+ (for building the frontend)

### Installation

1. **Backend Setup**
   ```bash
   pip install -r requirements.txt
   ```
   Create `.streamlit/secrets.toml` (optional, for AI features):
   ```toml
   OPENAI_API_KEY = "sk-..."
   ```

2. **Frontend Setup**
   ```bash
   cd diagram-prototype
   npm install
   npm run build
   ```

3. **Run the App**
   ```bash
   # From the root directory
   streamlit run app.py
   ```

## Development

- **Frontend Dev**: Run `npm run dev` in `diagram-prototype/` and set `MIRO_DEV_URL=http://localhost:5173` before running Streamlit to enable hot-reloading.
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical documentation.

## License
[Your License Here]
