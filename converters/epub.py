import sqlite3
import os
import re
import copy
from ebooklib import epub
from urllib.parse import urldefrag
from lxml import html, etree
from converters.utils import (
    setup_database, parse_parts, parse_footnote_markers, 
    get_part, get_page_reset_ids, clean_content_text, clean_toc_title,
    wrap_direction, parse_skip_ids
)

def walk_toc(entries, toc_entries, lvl=1, parent_toc_index=None):
    for entry in entries:
        if isinstance(entry, epub.Link):
            file, anchor = urldefrag(entry.href)
            toc_entries.append({
                "title":             entry.title,
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
                "title":             section.title,
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

def process_epub(epub_path, db_path, book_id="00000", page_marker=None, 
                 footnote_markers_str=None, parts_str=None,
                 collapse_newlines=False, clean_toc=False, fix_cap=False,
                 detect_dir=False, skip_ids_str=None, max_len_skip=0,
                 progress_callback=None, footnote_separator=None):
    
    footnote_markers = parse_footnote_markers(footnote_markers_str)
    part_boundaries = parse_parts(parts_str)
    page_reset_ids  = get_page_reset_ids(part_boundaries)
    skip_ids_set    = parse_skip_ids(skip_ids_str)

    book = epub.read_epub(epub_path)
    toc_entries = []
    walk_toc(book.toc, toc_entries)

    conn, cur, table_b, table_t = setup_database(db_path, book_id)

    global_id           = 1
    source_page_counter = 1
    current_page_number = 1
    xhtml_cache         = {}
    processed_locations = {}
    processed_titles    = {}

    total_entries = len(toc_entries)
    for idx, entry in enumerate(toc_entries):
        if progress_callback:
            progress_callback(idx / total_entries, f"Memproses bab {idx+1}/{total_entries}: {entry['title']}")
            
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
                        chunk_clean = clean_content_text(clean_chunk, collapse_newlines=collapse_newlines, footnote_separator=footnote_separator)
                        chunk_clean = wrap_direction(chunk_clean, enable=detect_dir)
                        if not chunk_clean:
                            continue

                        # SKIP LOGIC
                        should_skip = False
                        if source_page_counter in skip_ids_set:
                            should_skip = True
                        if max_len_skip > 0 and len(chunk_clean) > max_len_skip:
                            should_skip = True
                            
                        if should_skip:
                            source_page_counter += 1
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
                        source_page_counter += 1
                        current_page_number += 1

                    if location_key not in processed_locations:
                        processed_locations[location_key] = toc_link_id or 0

        raw_tit = entry["title"]
        clean_tit = clean_toc_title(raw_tit, remove_numbers=clean_toc, fix_capitalization=fix_cap)
        
        if toc_link_id == 0 and location_key in processed_locations:
            toc_link_id = processed_locations[location_key]

        if clean_tit and clean_tit not in processed_titles:
            cur.execute(
                f"INSERT INTO {table_t} (tit, lvl, sub, id) VALUES (?, ?, ?, ?)",
                (clean_tit, entry["lvl"], 0, toc_link_id),
            )
            processed_titles[clean_tit] = cur.lastrowid

    conn.commit()
    conn.close()
    return True
