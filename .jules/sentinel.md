## 2024-05-30 - Arbitrary File Write via Path Traversal in Streamlit File Uploader
**Vulnerability:** The application used `os.path.join(tempfile.gettempdir(), os.path.splitext(uploaded_file.name)[0] + ".sqlite")` to generate output file paths.
**Learning:** `uploaded_file.name` is derived from user input and can contain path traversal characters (e.g., `../../../`). This allows an attacker to control the destination path of the generated SQLite file, leading to arbitrary file write.
**Prevention:** Never use user-provided filenames directly in server-side file paths. Always use `tempfile.mkstemp()` or `tempfile.NamedTemporaryFile()` for temporary files, or sanitize the input using `os.path.basename()` before appending to a directory path.

## 2024-05-30 - Information Leakage via Stack Traces in Streamlit
**Vulnerability:** The application used `st.exception(e)` to render exceptions in the UI, and passed the raw exception object `e` to `st.error()` and `st.toast()`.
**Learning:** `st.exception(e)` displays full internal stack traces and server environment paths to end users, exposing sensitive internal structure that attackers can use to craft targeted attacks. Passing raw exception objects into string formatting or UI components can also expose sensitive data.
**Prevention:** Avoid using `st.exception()` in production applications. Always catch exceptions, log the full error stack internally using `logging.error(..., exc_info=e)`, and present a sanitized, generic error message (e.g., using just the exception class name) to the user via `st.error()` or `st.toast()`.
