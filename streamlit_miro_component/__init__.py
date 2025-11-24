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
        # Fallback or error if build missing
        pass 
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
