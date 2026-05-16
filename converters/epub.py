import sqlite3
import os
import re
import copy
from ebooklib import epub
from urllib.parse import urldefrag
from lxml import html, etree

# ================================================================
# HELPERS & LOGIC (Refactored from original script)
# ================================================================

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

def clean_title_text(text):
    if not text:
        return ""
    chars_to_remove = [chr(8207), chr(8206), chr(8203), chr(160)]
    for c in chars_to_remove:
        text = text.replace(c, "")
    return text.strip()

def walk_toc(entries, toc_entries, lvl=1, parent_toc_index=None):
    for entry in entries:
        if isinstance(entry, epub.Link):
            file, anchor = urldefrag(entry.href)
            toc_entries.append({
                "title":             clean_title_text(entry.title),
                "file":              file,
                "anchor":            anchor if anchor else None,
                "lvl":               lvl,
                "parent_toc_index":  parent_toc_index,
            })
        elif isinstance(entry, tuple):
            section, children = entry
            file, anchor = urldefrag(section.href)
            my_index = len(toc_entries)
            toc_entries.append({
                "title":             clean_title_text(section.title),
                "file":              file,
                "anchor":            anchor if anchor else None,
                "lvl":               lvl,
                "parent_toc_index":  parent_toc_index,
            })
            walk_toc(children, toc_entries, lvl + 1, my_index)

def load_xhtml(book, xhtml_cache, file):
    if file in xhtml_cache:
        return xhtml_cache[file]
    try:
        item = book.get_item_with_href(file)
        if not item:
            return None
        doc = html.fromstring(item.get_content())
        xhtml_cache[file] = doc
        return doc
    except Exception:
        return None

def clean_html_tree(element):
    tags_to_strip = [
        "div", "span", "section", "article",
        "header", "footer", "a",
        "h1", "h2", "h3", "h4", "h5", "h6", "p",
    ]
    etree.strip_tags(element, *tags_to_strip)
    for tag in element.iter():
        tag.attrib.clear()

def get_inner_html(element):
    parts = []
    if element.text:
        parts.append(element.text)
    for child in element:
        parts.append(etree.tostring(child, encoding="unicode", method="html"))
    return "".join(parts)

def extract_section(doc, anchor, next_anchor):
    body = doc.find("body")
    if body is None:
        return "", "", []

    content_parts = []

    if not anchor:
        iterator = body.iterchildren()
        for el in iterator:
            if next_anchor:
                if el.get("id") == next_anchor:
                    break
                if el.xpath(f".//*[@id='{next_anchor}']"):
                    break
            content_parts.append(copy.deepcopy(el))
    else:
        start_elems = doc.xpath(f"//*[@id='{anchor}']")
        if not start_elems:
            return "", "", []
        start_node = start_elems[0]
        content_parts.append(copy.deepcopy(start_node))
        for el in start_node.itersiblings():
            if next_anchor:
                if el.get("id") == next_anchor:
                    break
                if el.xpath(f".//*[@id='{next_anchor}']"):
                    break
            content_parts.append(copy.deepcopy(el))

    temp_wrapper = etree.Element("div")
    for el in content_parts:
        temp_wrapper.append(el)

    raw_html = etree.tostring(temp_wrapper, encoding="unicode", method="html")
    ids_included = [e.get("id") for e in temp_wrapper.xpath("//*[@id]") if e.get("id")]

    clean_copy = copy.deepcopy(temp_wrapper)
    clean_html_tree(clean_copy)
    clean_inner = get_inner_html(clean_copy).strip()

    return clean_inner, raw_html, ids_included

def split_into_chunks(clean_inner, raw_html, page_marker, footnote_markers):
    if page_marker and page_marker in raw_html:
        raw_splits  = raw_html.split(page_marker)
        clean_splits = clean_inner.split(page_marker)
    else:
        return [clean_inner], [raw_html]

    if len(raw_splits) != len(clean_splits):
        return [clean_inner], [raw_html]

    final_clean = []
    final_raw   = []

    current_clean = clean_splits[0]
    current_raw   = raw_splits[0]

    for i in range(1, len(clean_splits)):
        next_clean = clean_splits[i]
        next_raw   = raw_splits[i]

        clean_lines = next_clean.split("\n")
        raw_lines   = next_raw.split("\n")

        footnote_clean = []
        footnote_raw   = []
        body_clean     = []
        body_raw       = []

        scanning = True
        for j, line in enumerate(clean_lines):
            stripped = line.strip()
            is_footnote = any(stripped.startswith(m) for m in footnote_markers) if footnote_markers else False
            if scanning:
                if is_footnote or stripped == "":
                    footnote_clean.append(line)
                    if j < len(raw_lines):
                        footnote_raw.append(raw_lines[j])
                else:
                    scanning = False
                    body_clean.append(line)
                    if j < len(raw_lines):
                        body_raw.append(raw_lines[j])
            else:
                body_clean.append(line)
                if j < len(raw_lines):
                    body_raw.append(raw_lines[j])

        if footnote_clean:
            current_clean += "\n" + "\n".join(footnote_clean)
            current_raw   += "\n" + "\n".join(footnote_raw)

        final_clean.append(current_clean)
        final_raw.append(current_raw)

        current_clean = "\n".join(body_clean)
        current_raw   = "\n".join(body_raw)

    final_clean.append(current_clean)
    final_raw.append(current_raw)

    return final_clean, final_raw

# ================================================================
# MAIN ENTRY POINT FOR WEB/EXTERNAL
# ================================================================

def process_epub(epub_path, db_path, book_id="00000", page_marker=None, footnote_markers_str=None, parts_str=None):
    footnote_markers = parse_footnote_markers(footnote_markers_str)
    part_boundaries = parse_parts(parts_str)
    page_reset_ids  = get_page_reset_ids(part_boundaries)

    book = epub.read_epub(epub_path)
    toc_entries = []
    walk_toc(book.toc, toc_entries)

    conn, cur, table_b, table_t = setup_database(db_path, book_id)

    global_id           = 1
    current_page_number = 1
    xhtml_cache         = {}
    processed_locations = {}
    processed_titles    = {}

    for idx, entry in enumerate(toc_entries):
        location_key = (entry["file"], entry["anchor"])
        toc_link_id  = 0

        if location_key in processed_locations:
            toc_link_id = processed_locations[location_key]
        else:
            doc = load_xhtml(book, xhtml_cache, entry["file"])
            if doc is None:
                processed_locations[location_key] = 0
            else:
                next_anchor = None
                if idx + 1 < len(toc_entries):
                    nxt = toc_entries[idx + 1]
                    if nxt["file"] == entry["file"] and nxt["anchor"]:
                        next_anchor = nxt["anchor"]

                clean_inner, raw_html, _ = extract_section(doc, entry["anchor"], next_anchor)

                if not clean_inner and not raw_html:
                    processed_locations[location_key] = 0
                else:
                    clean_chunks, raw_chunks = split_into_chunks(
                        clean_inner, raw_html, page_marker, footnote_markers
                    )

                    first_assigned = False

                    for raw_chunk, clean_chunk in zip(raw_chunks, clean_chunks):
                        chunk_clean = clean_chunk.strip()
                        if not chunk_clean:
                            continue

                        if global_id in page_reset_ids:
                            current_page_number = 1

                        part = get_part(global_id, part_boundaries)

                        cur.execute(
                            f"INSERT INTO {table_b} (nass, part, id, page) VALUES (?, ?, ?, ?)",
                            (chunk_clean, part, global_id, current_page_number),
                        )

                        if not first_assigned:
                            toc_link_id    = global_id
                            first_assigned = True

                        found_ids = re.findall(r'id=["\']([^"\']+)["\']', raw_chunk or "")
                        for aid in found_ids:
                            key = (entry["file"], aid)
                            if key not in processed_locations:
                                processed_locations[key] = global_id

                        global_id           += 1
                        current_page_number += 1

                    if location_key not in processed_locations:
                        processed_locations[location_key] = toc_link_id or 0

        clean_tit = entry["title"]
        if toc_link_id == 0 and location_key in processed_locations:
            toc_link_id = processed_locations[location_key]

        if clean_tit not in processed_titles:
            cur.execute(
                f"INSERT INTO {table_t} (tit, lvl, sub, id) VALUES (?, ?, ?, ?)",
                (clean_tit, entry["lvl"], 0, toc_link_id),
            )
            processed_titles[clean_tit] = cur.lastrowid

    conn.commit()
    conn.close()
    return True
