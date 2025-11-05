import json
import os
from typing import Any, Dict, Optional

import streamlit as st
import streamlit.components.v1 as components


_build_dir = os.path.join(os.path.dirname(__file__), "build")
_dev_url = os.environ.get("MIRO_DEV_URL")
if _dev_url:
    _miro_component = components.declare_component("miro_board", url=_dev_url)
else:
    if not os.path.exists(_build_dir):
        raise RuntimeError("Component build not found. Run npm run build in streamlit_miro_component/frontend.")
    _miro_component = components.declare_component("miro_board", path=_build_dir)


def miro_board(initial_board: Optional[Dict[str, Any]] = None, key: Optional[str] = None) -> Dict[str, Any]:
    if initial_board is None:
        initial_board = {"nodes": [], "edges": [], "selection": []}
    result = _miro_component(board=initial_board, key=key, default=initial_board)
    if not isinstance(result, dict):
        return initial_board
    return result


__all__ = ["miro_board"]


