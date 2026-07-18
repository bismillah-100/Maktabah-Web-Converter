## 2024-05-30 - Arbitrary File Write via Path Traversal in Streamlit File Uploader
**Vulnerability:** The application used `os.path.join(tempfile.gettempdir(), os.path.splitext(uploaded_file.name)[0] + ".sqlite")` to generate output file paths.
**Learning:** `uploaded_file.name` is derived from user input and can contain path traversal characters (e.g., `../../../`). This allows an attacker to control the destination path of the generated SQLite file, leading to arbitrary file write.
**Prevention:** Never use user-provided filenames directly in server-side file paths. Always use `tempfile.mkstemp()` or `tempfile.NamedTemporaryFile()` for temporary files, or sanitize the input using `os.path.basename()` before appending to a directory path.

## 2024-05-30 - Information Leakage via Stack Traces in Streamlit
**Vulnerability:** The application used `st.exception(e)` to render exceptions in the UI, and passed the raw exception object `e` to `st.error()` and `st.toast()`.
**Learning:** `st.exception(e)` displays full internal stack traces and server environment paths to end users, exposing sensitive internal structure that attackers can use to craft targeted attacks. Passing raw exception objects into string formatting or UI components can also expose sensitive data.
**Prevention:** Avoid using `st.exception()` in production applications. Always catch exceptions, log the full error stack internally using `logging.error(..., exc_info=e)`, and present a sanitized, generic error message (e.g., using just the exception class name) to the user via `st.error()` or `st.toast()`.
## 2024-07-04 - XPath Injection in EPUB Parser
**Vulnerability:** String-interpolated XPath queries in `converters/epub.py` (`doc.xpath(f"//*[@id='{anchor}']")`) allowed potential XPath injection if an EPUB contained maliciously crafted anchor IDs.
**Learning:** `lxml`'s `xpath()` function evaluates the entire string. If user-controlled data (like EPUB anchor IDs) is injected directly via f-strings, it can break out of the string literal and alter the query structure.
**Prevention:** Always use parameterized XPath variables for dynamic values (e.g., `doc.xpath("//*[@id=$anc]", anc=anchor)`) to ensure the input is treated strictly as a string literal by the XPath engine.

## 2026-07-08 - SQL Injection in Dynamic Table Names
**Vulnerability:** SQL Injection in DML Queries due to unvalidated `book_id` being interpolated into table names.
**Learning:** Using user-provided strings to construct table names (e.g., `f"b{book_id}"`) can lead to SQL injection if not properly sanitized, even if parameterization is used for values.
**Prevention:** Always validate and sanitize variables used for table names. In Python, ensure identifiers match a safe regex pattern like `^\w+$` before concatenating them into SQL statements.
## 2026-07-11 - Stored XSS via Incomplete HTML Tag Stripping
**Vulnerability:** The `clean_html_tree` function in `converters/epub.py` used `etree.strip_tags()` and `tag.attrib.clear()` but failed to remove dangerous tags like `<script>` or `<style>` and their content, allowing Stored Cross-Site Scripting (XSS).
**Learning:** `lxml`'s `strip_tags()` only removes the tags themselves and keeps the inner text. Unstripped dangerous tags (and their content) were being preserved in the HTML output, presenting an XSS risk when rendered in a WebView.
**Prevention:** Always use `etree.strip_elements()` to completely remove dangerous tags AND their content (like `script`, `style`, `iframe`, `object`) before applying formatting cleanup via `strip_tags()`.
## 2024-07-18 - [Disk Exhaustion DoS via Orphaned Temporary Files]
**Vulnerability:** The application was failing to guarantee the cleanup of temporary files (`input_path` and `output_path`) in Streamlit file uploads when an exception occurred during the conversion process, leading to a Disk Exhaustion Denial of Service (DoS) vulnerability.
**Learning:** In cloud environments like Streamlit Cloud, disk space is limited. Relying on linear execution flow `os.remove()` at the end of a block without `finally` leaves the system vulnerable to accumulated orphaned files if any step fails.
**Prevention:** Always use a robust `try...except...finally` structure for temporary file handling. Ensure `os.remove()` is called in the `finally` block to guarantee execution regardless of exceptions.
