import os
from typing import List, Dict, Tuple

import streamlit as st


Record = Dict[str, str]


def scan_dummy_data(root: str = "sample_data") -> List[Record]:
    """Scan a folder of sample files and build a simple in-memory index.

    Each record contains: path, name, ext, text (best-effort content or filename).
    """
    records: List[Record] = []
    if not os.path.isdir(root):
        return records
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            path = os.path.join(dirpath, fname)
            ext = os.path.splitext(fname)[1].lower().strip(".")
            text = _read_best_effort(path, ext)
            records.append({
                "path": path,
                "name": fname,
                "ext": ext,
                "text": text or fname,
            })
    return records


def _read_best_effort(path: str, ext: str) -> str:
    try:
        if ext in {"txt", "md", "csv"}:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        # Binary or complex formats: just return empty; we will search on filename
        return ""
    except Exception:
        return ""


def search_files(query: str, records: List[Record], k: int = 5) -> List[Record]:
    """Very simple keyword search over text and filename; returns top-k matches."""
    if not query:
        return []
    q = query.lower()
    scored: List[Tuple[int, Record]] = []
    for r in records:
        hay = f"{r.get('name','')}\n{r.get('text','')}".lower()
        score = hay.count(q)
        if score == 0 and any(tok in hay for tok in q.split()):
            score = 1
        if score > 0:
            scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:k]]


def icon_for_ext(ext: str) -> str:
    mapping = {
        "pdf": "📄",
        "doc": "📝",
        "docx": "📝",
        "xls": "📊",
        "xlsx": "📊",
        "csv": "🧾",
        "txt": "📄",
        "md": "🗒️",
        "ppt": "📈",
        "pptx": "📈",
        "png": "🖼️",
        "jpg": "🖼️",
        "jpeg": "🖼️",
        "gif": "🖼️",
        "json": "🧩",
    }
    return mapping.get(ext.lower(), "📁")


def looks_like_search(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    return any(w in t for w in ["find", "search", "look for", "show me", "list "])


def render_results(results: List[Record]) -> None:
    if not results:
        st.info("No matching documents found.")
        return
    for doc in results:
        icon = icon_for_ext(doc.get("ext", ""))
        st.write(f"{icon} **{doc.get('name','')}**")
        st.caption(doc.get("path", ""))


