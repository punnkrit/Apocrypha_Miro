import json
import os
from typing import Any, Dict, Optional

import streamlit as st
import streamlit.components.v1 as components


# Point to the diagram-prototype dist folder
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_build_dir = os.path.join(_root, "diagram-prototype", "dist")

_dev_url = os.environ.get("MIRO_DEV_URL")

if _dev_url:
    _miro_component = components.declare_component("miro_board", url=_dev_url)
else:
    if not os.path.exists(_build_dir):
        error_msg = f"""
        ❌ **Component Build Missing**
        
        The `diagram-prototype/dist` directory was not found at: `{_build_dir}`
        
        **To fix this:**
        1. Navigate to the `diagram-prototype` directory
        2. Run: `npm install` (if not already done)
        3. Run: `npm run build`
        4. Ensure the `dist` folder is committed to git (check .gitignore)
        5. For Streamlit Cloud: The `dist` folder must be in your repository
        
        **For local development:**
        - Set `MIRO_DEV_URL=http://localhost:5173` environment variable
        - Run `npm run dev` in the `diagram-prototype` directory
        """
        raise FileNotFoundError(error_msg)
    
    # Verify the dist folder has the required files
    index_html = os.path.join(_build_dir, "index.html")
    if not os.path.exists(index_html):
        raise FileNotFoundError(
            f"Build directory exists but is missing index.html at {index_html}. "
            "Please run `npm run build` in the diagram-prototype directory."
        )
    
    _miro_component = components.declare_component("miro_board", path=_build_dir)


def miro_board(nodes: list = None, edges: list = None, highlight_nodes: list = None, key: Optional[str] = None) -> Dict[str, Any]:
    """
    Wrapper for the React Flow component.
    """
    if nodes is None: nodes = []
    if edges is None: edges = []
    if highlight_nodes is None: highlight_nodes = []
    
    # We pass arguments as named parameters which become 'args' in the frontend
    component_value = _miro_component(
        nodes=nodes, 
        edges=edges, 
        highlight_nodes=highlight_nodes, 
        key=key,
        default={}
    )
    
    return component_value if component_value else {}

__all__ = ["miro_board"]
