import sqlite3
import re

# ⚡ Bolt: Precompiled regular expressions for better string processing performance
COLLAPSE_NEWLINES_RE = re.compile(r'\n\s*\n+')
ARABIC_CHAR_RE = re.compile(r'[\u0600-\u06FF]')
LEADING_NUMBERS_RE = re.compile(r'^\d+[\.\s]*')
CAPITALIZE_RE = re.compile(r"[A-Za-z]+('[A-Za-z]+)?")
LATIN_CHAR_RE = re.compile(r'[a-zA-Z]')

def parse_parts(parts_str):
    if not parts_str:
        return []
    result = []
    for segment in parts_str.split(","):
        segment = segment.strip()
        if not segment:
            continue
        try:
            start_id, part_num = segment.split(":")
            result.append((int(start_id.strip()), int(part_num.strip())))
        except ValueError:
            pass
    result.sort(key=lambda x: x[0])
    return result

def parse_footnote_markers(markers_str):
    if not markers_str:
        return []
    return [m.strip() for m in markers_str.split(",") if m.strip()]

def setup_database(db_path, book_id):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    table_b = f"b{book_id}"
    table_t = f"t{book_id}"
    cur.executescript(f"""
        DROP TABLE IF EXISTS {table_b};
        DROP TABLE IF EXISTS {table_t};

        CREATE TABLE {table_b} (
            nass TEXT COLLATE NOCASE,
            part INTEGER,
            id   INTEGER,
            page INTEGER
        );

        CREATE TABLE {table_t} (
            tit TEXT COLLATE NOCASE,
            lvl INTEGER,
            sub INTEGER,
            id  INTEGER
        );
    """)
    conn.commit()
    return conn, cur, table_b, table_t

def get_part(global_id, part_boundaries):
    if not part_boundaries:
        return 1
    part = part_boundaries[0][1]
    for start_id, part_num in part_boundaries:
        if global_id >= start_id:
            part = part_num
        else:
            break
    return part

def get_page_reset_ids(part_boundaries):
    if not part_boundaries:
        return set()
    return {start_id for start_id, _ in part_boundaries[1:]}

def clean_content_text(text, collapse_newlines=False, footnote_separator=None):
    if not text:
        return ""
    
    if footnote_separator:
        lines = text.split("\n")
        new_lines = []
        target = footnote_separator.strip()
        for line in lines:
            if line.strip() == target:
                new_lines.append("__________")
            else:
                new_lines.append(line)
        text = "\n".join(new_lines)

    if collapse_newlines:
        # Replace 2 or more newlines with a single newline
        text = COLLAPSE_NEWLINES_RE.sub('\n', text)
    return text.strip()

def is_arabic(text):
    # Basic check for Arabic characters range
    return bool(ARABIC_CHAR_RE.search(text))

def clean_toc_title(title, remove_numbers=False, fix_capitalization=False):
    if not title:
        return ""
    
    res = title.strip()
    
    if remove_numbers:
        # Remove leading numbers followed by dots, spaces or directly text
        # e.g. "0018. Judul" -> "Judul", "1. Judul" -> "Judul"
        res = LEADING_NUMBERS_RE.sub('', res).strip()
    
    if fix_capitalization and not is_arabic(res):
        # Improved Title Case that doesn't capitalize after apostrophes
        # res.title() makes "Al-Qur'an" -> "Al-Qur'An"
        # We use regex to capitalize only the first letter of each word
        res = CAPITALIZE_RE.sub(lambda mo: mo.group(0).capitalize(), res)
        
    return res

def parse_skip_ids(skip_str):
    if not skip_str:
        return set()
    ids = set()
    for segment in skip_str.split(","):
        segment = segment.strip()
        if not segment:
            continue
        if "-" in segment:
            try:
                start, end = map(int, segment.split("-"))
                ids.update(range(start, end + 1))
            except ValueError:
                pass
        else:
            try:
                ids.add(int(segment))
            except ValueError:
                pass
    return ids

def wrap_direction(text, enable=False):
    if not enable or not text:
        return text
    
    lines = text.split("\n")
    wrapped_lines = []
    
    # Unicode Control Characters
    LRE = "\u202A" # Left-to-Right Embedding
    RLE = "\u202B" # Right-to-Left Embedding
    PDF = "\u202C" # Pop Directional Formatting (Closer)
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            wrapped_lines.append(line)
            continue
            
        # Count Latin vs Arabic/RTL
        latin_count = len(LATIN_CHAR_RE.findall(stripped))
        arabic_count = len(ARABIC_CHAR_RE.findall(stripped))
        
        if latin_count > arabic_count:
            # Predominantly LTR
            wrapped_lines.append(f"{LRE}{stripped}{PDF}")
        else:
            # Predominantly RTL
            wrapped_lines.append(f"{RLE}{stripped}{PDF}")
            
    return "\n".join(wrapped_lines)
