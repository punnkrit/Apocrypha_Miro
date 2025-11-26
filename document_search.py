import os
from typing import List, Dict, Tuple

import streamlit as st
from pypdf import PdfReader

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
        elif ext == "pdf":
            try:
                reader = PdfReader(path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
            except Exception:
                return ""
        # Binary or complex formats: just return empty; we will search on filename
        return ""
    except Exception:
        return ""


def search_files(
    query: str,
    records: List[Record],
    k: int = 50,
    context_folders: List[str] = None,
    industry_filter: str = None,
) -> List[Record]:
    """Improved keyword search with context filtering and better scoring.
    
    Args:
        query: Search query string
        records: List of document records
        k: Maximum number of results
        context_folders: Optional list of folders to restrict search to
        industry_filter: Optional industry folder to filter by (e.g., "Restaurant_Franchise" or "Legal_Firm")
    """
    if not query:
        return []
    
    q = query.lower()
    query_words = set(q.split())
    
    # First, filter by industry if specified
    if industry_filter:
        records = [r for r in records if industry_filter in r.get("path", "")]
    
    # Extract location and category from query (for F&B)
    locations = {"west": "west", "central": "central", "east": "east"}
    fnb_categories = {
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
    
    # Legal firm keywords
    legal_practice_areas = {
        "corporate": "corporate_law",
        "m&a": "corporate_law",
        "merger": "corporate_law",
        "acquisition": "corporate_law",
        "ipo": "corporate_law",
        "litigation": "litigation",
        "lawsuit": "litigation",
        "dispute": "litigation",
        "court": "litigation",
        "real estate": "real_estate",
        "property": "real_estate",
        "lease": "real_estate",
        "zoning": "real_estate",
        "ip": "intellectual_property",
        "intellectual property": "intellectual_property",
        "patent": "intellectual_property",
        "trademark": "intellectual_property",
        "copyright": "intellectual_property",
        "employment": "employment_law",
        "compensation": "employment_law",
        "workplace": "employment_law",
        "hr": "employment_law",
        "investigation": "employment_law",
    }
    
    # Legal matter keywords
    legal_matters = {
        "techcorp": "techcorp_acquisition",
        "globalretail": "globalretail_ipo",
        "smith": "smith_v_megacorp",
        "megacorp": "smith_v_megacorp",
        "abc": "contractdispute",
        "xyz": "contractdispute",
        "contract dispute": "contractdispute",
        "tower": "downtown_tower",
        "downtown": "downtown_tower",
        "office lease": "office_lease",
        "biotech": "patent_portfolio_biotech",
        "patent portfolio": "patent_portfolio",
        "trademark dispute": "trademark_dispute",
        "fashion": "trademark_dispute_fashion",
        "executive": "executive_compensation",
        "compensation review": "executive_compensation",
        "workplace investigation": "workplace_investigation",
    }
    
    query_location = None
    query_category = None
    query_practice_area = None
    query_matter = None
    
    # Check for F&B keywords
    for word in query_words:
        for loc_key, loc_val in locations.items():
            if loc_key in word:
                query_location = loc_val
                break
        for cat_key, cat_val in fnb_categories.items():
            if cat_key in word:
                query_category = cat_val
                break
    
    # Check for Legal keywords (check full query for multi-word matches)
    for key, val in legal_practice_areas.items():
        if key in q:
            query_practice_area = val
            break
    
    for key, val in legal_matters.items():
        if key in q:
            query_matter = val
            break
    
    # Filter records by context folders if provided
    filtered_records = records
    if context_folders:
        filtered_records = []
        for r in records:
            path = r.get("path", "").lower()
            for folder in context_folders:
                folder_lower = folder.lower()
                if folder_lower.replace("_", "") in path.replace("_", "").replace("/", ""):
                    filtered_records.append(r)
                    break
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
            if len(word) > 2:  # Skip very short words
                if word in hay:
                    score += 2.0
                if word in name:
                    score += 3.0
        
        # F&B path matching
        path_score = 0.0
        
        if query_location and query_location in path:
            path_score += 10.0
        
        if query_category and query_category in path:
            path_score += 10.0
            
        if query_location and query_category:
            if (query_location in path) and (query_category in path):
                path_score += 15.0
            else:
                path_score -= 5.0
        elif query_category and not query_location:
            if query_category in path:
                path_score += 15.0
        
        # Legal practice area matching
        if query_practice_area and query_practice_area.replace("_", "") in path.replace("_", ""):
            path_score += 20.0
        
        # Legal matter matching
        if query_matter and query_matter.replace("_", "") in path.replace("_", ""):
            path_score += 25.0
        
        score += path_score
        
        # Category name matching in filename
        if query_category:
            for cat_key, cat_val in fnb_categories.items():
                if cat_key in name and cat_val == query_category:
                    score += 5.0
        
        # Time period matching
        time_indicators = ["q1", "q2", "q3", "q4", "march", "april", "may", "2023", "2024", "2025"]
        for indicator in time_indicators:
            if indicator in query_words and indicator in hay:
                score += 3.0
        
        # Only add if score is positive
        if score > 0:
            r_with_score = r.copy()
            r_with_score["score"] = score
            scored.append((score, r_with_score))
    
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


def extract_node_ids_from_paths(paths: List[str], industry: str = "fnb") -> List[str]:
    """Extract board node IDs from document paths.
    
    For F&B: Maps paths like 'sample_data/Restaurant_Franchise/East_Group/Accounting/file.pdf' 
             to node IDs like 'east_accounting'.
    For Legal: Maps paths like 'sample_data/Legal_Firm/Intellectual_Property/Trademark_Dispute_Fashion/file.pdf'
               to node IDs like 'intellectual_property_trademark_dispute_fashion'.
    """
    node_ids = []
    
    for path in paths:
        path_lower = path.lower()
        path_parts = path_lower.replace("\\", "/").split("/")
        
        if "restaurant_franchise" in path_lower:
            # F&B structure
            group = None
            category = None
            
            for part in path_parts:
                part_clean = part.replace("_", "").replace("-", "")
                
                if not group:
                    if "westgroup" in part_clean:
                        group = "west"
                    elif "centralgroup" in part_clean:
                        group = "central"
                    elif "eastgroup" in part_clean:
                        group = "east"
                
                if not category:
                    if "accounting" in part_clean:
                        category = "accounting"
                    elif "expenses" in part_clean:
                        category = "expenses"
                    elif part_clean == "legal":
                        category = "legal"
                    elif "permits" in part_clean:
                        category = "permits"
            
            if group and category:
                node_id = f"{group}_{category}"
                if node_id not in node_ids:
                    node_ids.append(node_id)
                    
        elif "legal_firm" in path_lower:
            # Legal firm structure
            practice_area = None
            matter = None
            
            # Practice area mappings
            practice_area_map = {
                "corporate_law": "corporate_law",
                "litigation": "litigation",
                "real_estate": "real_estate",
                "intellectual_property": "intellectual_property",
                "employment_law": "employment_law",
            }
            
            # Matter mappings (folder name -> matter id part)
            matter_map = {
                "techcorp_acquisition": "techcorp_acquisition",
                "globalretail_ipo": "globalretail_ipo",
                "smith_v_megacorp": "smith_v_megacorp",
                "contractdispute_abcvxyz": "contractdispute_abcvxyz",
                "downtown_tower_development": "downtown_tower_development",
                "office_lease_negotiation": "office_lease_negotiation",
                "patent_portfolio_biotech": "patent_portfolio_biotech",
                "trademark_dispute_fashion": "trademark_dispute_fashion",
                "executive_compensation_review": "executive_compensation_review",
                "workplace_investigation": "workplace_investigation",
            }
            
            for part in path_parts:
                part_normalized = part.replace("-", "_")
                
                if not practice_area:
                    for key in practice_area_map:
                        if key == part_normalized:
                            practice_area = practice_area_map[key]
                            break
                
                if not matter:
                    for key in matter_map:
                        if key == part_normalized:
                            matter = matter_map[key]
                            break
            
            # Build full node ID for legal matters
            if practice_area and matter:
                node_id = f"{practice_area}_{matter}"
                if node_id not in node_ids:
                    node_ids.append(node_id)
    
    return node_ids


