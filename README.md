# Streamlit + React Miro-like Board (Demo)

Minimal Streamlit app embedding a React (Vite + TypeScript) custom component that provides a simple Miro-like board and a chat panel using OpenAI `gpt-3.5-turbo`.

## Setup

1) Ensure Streamlit secrets contain your OpenAI key:

```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "sk-..."
```

2) Install Python deps:

```bash
pip install -r requirements.txt
```

3) Build the frontend component:

```bash
cd streamlit_miro_component/frontend
npm install
npm run build
```

This produces `streamlit_miro_component/build/` which the Python component loads.

4) Run the app:

```bash
cd ../../..
streamlit run app.py
```

## Notes
- Board supports pan (drag background), wheel zoom, and dragging nodes.
- Use the Seed button to populate example nodes.
- Chat grounds answers in the current board JSON and is allowed to “act as if it can do anything” for demo purposes.

