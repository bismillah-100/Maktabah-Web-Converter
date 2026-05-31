## 2024-05-30 - Arbitrary File Write via Path Traversal in Streamlit File Uploader
**Vulnerability:** The application used `os.path.join(tempfile.gettempdir(), os.path.splitext(uploaded_file.name)[0] + ".sqlite")` to generate output file paths.
**Learning:** `uploaded_file.name` is derived from user input and can contain path traversal characters (e.g., `../../../`). This allows an attacker to control the destination path of the generated SQLite file, leading to arbitrary file write.
**Prevention:** Never use user-provided filenames directly in server-side file paths. Always use `tempfile.mkstemp()` or `tempfile.NamedTemporaryFile()` for temporary files, or sanitize the input using `os.path.basename()` before appending to a directory path.
