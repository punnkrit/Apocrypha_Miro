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


def search_files(
    query: str,
    records: List[Record],
    k: int = 5,
    context_folders: List[str] = None,
) -> List[Record]:
    """Improved keyword search with context filtering and better scoring."""
    if not query:
        return []
    
    q = query.lower()
    query_words = set(q.split())
    
    # Extract location and category from query
    locations = {"west": "west", "central": "central", "east": "east"}
    categories = {
        "accounting": "accounting",
        "expense": "expenses",
        "expenses": "expenses",
        "legal": "legal",
        "permit": "permits",
        "permits": "permits",
        "financial": "accounting",
        "finance": "accounting",
        "payroll": "accounting",
        "tax": "accounting",
    }
    
    query_location = None
    query_category = None
    for word in query_words:
        for loc_key, loc_val in locations.items():
            if loc_key in word:
                query_location = loc_val
                break
        for cat_key, cat_val in categories.items():
            if cat_key in word:
                query_category = cat_val
                break
    
    # Filter records by context folders if provided
    filtered_records = records
    if context_folders:
        filtered_records = []
        for r in records:
            path = r.get("path", "").lower()
            for folder in context_folders:
                folder_lower = folder.lower()
                # Match folder name in path (e.g., "west_group" matches "west_group/accounting/...")
                if folder_lower.replace("_", "") in path.replace("_", "").replace("/", ""):
                    filtered_records.append(r)
                    break
        # If no matches in context, use all records
        if not filtered_records:
            filtered_records = records
    
    scored: List[Tuple[float, Record]] = []
    for r in filtered_records:
        path = r.get("path", "").lower()
        name = r.get("name", "").lower()
        text = r.get("text", "").lower()
        hay = f"{name}\n{text}"
        
        score = 0.0
        
        # Exact query match (highest weight)
        if q in hay:
            score += 10.0
        if q in name:
            score += 5.0
        
        # Word matching
        for word in query_words:
            if word in hay:
                score += 2.0
            if word in name:
                score += 3.0
        
        # Path matching (boost if path matches query location/category)
        if query_location and query_location in path:
            score += 8.0
        if query_category and query_category in path:
            score += 8.0
        
        # Category name matching in filename
        if query_category:
            for cat_key, cat_val in categories.items():
                if cat_key in name and cat_val == query_category:
                    score += 5.0
        
        # Time period matching (Q1, Q2, Q3, Q4, March, 2024, etc.)
        time_indicators = ["q1", "q2", "q3", "q4", "march", "april", "may", "2023", "2024"]
        for indicator in time_indicators:
            if indicator in query_words and indicator in hay:
                score += 3.0
        
        # Only add if score is positive
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


def extract_node_ids_from_paths(paths: List[str]) -> List[str]:
    """Extract board node IDs from document paths.
    
    Maps paths like 'sample_data/East_Group/Accounting/file.pdf' to node IDs like 'east_A'.
    """
    node_ids = []
    for path in paths:
        path_lower = path.lower()
        # Extract group and category from path segments
        path_parts = path_lower.split("/")
        
        group = None
        category = None
        
        # Check each path segment for group and category
        for part in path_parts:
            part_clean = part.replace("_", "").replace("-", "")
            
            # Check for group
            if not group:
                if "westgroup" in part_clean or (part == "west" and group is None):
                    group = "west"
                elif "centralgroup" in part_clean or (part == "central" and group is None):
                    group = "central"
                elif "eastgroup" in part_clean or (part == "east" and group is None):
                    group = "east"
            
            # Check for category
            if not category:
                if "accounting" in part_clean:
                    category = "A"
                elif "expenses" in part_clean or "expense" in part_clean:
                    category = "E"
                elif "legal" in part_clean:
                    category = "L"
                elif "permits" in part_clean or "permit" in part_clean:
                    category = "P"
        
        # Build node ID (e.g., "central_L" for Central_Group/Legal)
        if group and category:
            node_id = f"{group}_{category}"
            if node_id not in node_ids:
                node_ids.append(node_id)
    
    return node_ids


