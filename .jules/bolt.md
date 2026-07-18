## 2024-05-24 - Streamlit UI Update Overhead in Tight Loops
**Learning:** Calling Streamlit UI update functions (like `st.progress` or `st.text`) inside tight loops (like iterating over every paragraph in a DOCX file) drastically degrades performance because these updates are synchronous and involve WebSocket communication overhead. For a 10,000-paragraph document, this blocks the main thread 10,000 times.
**Action:** Always throttle UI updates in loops (e.g., updating only every `N` iterations, or limiting total updates to ~100 with `max(1, total // 100)`) to maintain fast backend processing speeds without sacrificing user feedback.
## 2024-05-24 - python-docx para.style.name is extremely slow
**Learning:** In the python-docx library, accessing `para.style.name` triggers an expensive XML traversal for *every single paragraph*, leading to severe performance bottlenecks (O(N) operation inside the main processing loop).
**Action:** When working with python-docx loops, build a style mapping from `doc.styles` (`{style.style_id: style.name}`) before the loop. Inside the loop, extract the internal style ID quickly via `para._p.pPr.pStyle.val if para._p.pPr is not None and para._p.pPr.pStyle is not None else None` and look it up in the dictionary. This provides a ~20x speedup for large documents.

## 2024-05-27 - Fast-path re.search() over re.findall()
**Learning:** Python's `re.findall()` for counting characters is significantly slower than `re.search()`, especially when iterating over thousands of lines. In document processing where a feature (like RTL detection) relies on regex character counting, doing this for *every line* introduces a massive bottleneck.
**Action:** When performing regex counting for document analysis, always precede it with a fast-path `re.search()` to skip the expensive counting entirely if the target pattern (e.g., Arabic characters) isn't present in the line or text chunk at all.

## 2024-05-24 - Unnecessary Deepcopy in lxml Processing
**Learning:** In `converters/epub.py`, `extract_section` makes two deep copies of the lxml element tree: one when appending to `content_parts`, and another when creating `clean_copy` from `temp_wrapper`. Since `temp_wrapper` is constructed fresh and `raw_html` is generated immediately as a string, the second deep copy is completely redundant because `temp_wrapper` can be safely modified in-place by `clean_html_tree` afterwards.
**Action:** Avoid redundant `copy.deepcopy()` operations on lxml etrees, as they are relatively expensive. Instead, construct a single working tree, serialize it to a string if you need the raw HTML, and then modify that working tree directly for the clean text extraction.
## 2024-05-18 - Fast XPath Ancestor Lookups in Loops
**Learning:** Using `el.xpath(f".//*[@id='{target}']")` inside a tight loop to check if an element contains a target ID forces `lxml` to re-parse and traverse the descendant tree O(N) times, creating a severe bottleneck during EPUB conversion (tested ~1.1s down to ~0.15s).
**Action:** When searching for when a sibling iteration reaches an element containing a target ID, query the target ID globally once (`doc.xpath()`), trace its `getparent()` chain into a `set()`, and simply check `if el in break_nodes` during iteration for fast O(1) matching.
## 2024-10-24 - Optimize SQLite row insertions with executemany()
**Learning:** Even when wrapped in a single transaction, executing `cur.execute()` for thousands of rows inside a Python loop incurs significant DB-API parsing and function call overhead.
**Action:** When performing bulk row insertions, always accumulate the rows into an in-memory list (or generator) and use `cur.executemany()` instead to bypass loop overhead, which can yield a measurable ~30-40% speedup on inserts.

## 2024-05-24 - Pre-compile Regex in Loops
**Learning:** Using `re.match` inside a loop evaluating thousands of items incurs repeated regex compilation/cache-lookup overhead.
**Action:** Always extract static regular expression patterns using `re.compile()` before entering a large loop, such as document parsing loops.
## 2026-07-18 - Prevent Contract Breakage When Removing Unused Outputs
**Learning:** When optimizing a function by removing an expensive, unused variable that is part of the return tuple, do not just return a dummy value (like an empty list) as it violates the function's output contract and can cause functional regressions for unknown callers.
**Action:** Always completely remove the variable from the return signature and update all associated call sites when eliminating an unused return value.
