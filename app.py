import streamlit as st
import os
import tempfile
from converters.epub import process_epub
from converters.docx import process_docx

# --- Multi-language Dictionary ---
TEXTS = {
    "id": {
        "title": "📚 Konverter E-Book ke SQLite",
        "header_desc": "Unggah file dokumen Anda untuk dikonversi menjadi format SQLite yang kompatibel dengan aplikasi Maktabah.",
        "config_header": "Opsi Konfigurasi",
        "page_marker_label": "Page Marker",
        "page_marker_help": "Karakter pemisah halaman (misal: @). Kosongkan jika tidak ada.",
        "footnote_markers_label": "Footnote Markers",
        "footnote_markers_help": "Karakter prefix footnote, dipisah koma.",
        "footnote_sep_label": "Footnote Separator",
        "footnote_sep_help": "Karakter pemisah footnote (misal: ---). Akan diubah menjadi '__________' jika baris tersebut hanya berisi karakter ini.",
        "parts_label": "Parts Definition",
        "parts_help": "Format: start_id:part_num,...",
        "cleaning_header": "Opsi Pembersihan",
        "collapse_newlines_label": "Hapus baris kosong berlebih",
        "collapse_newlines_help": "Menghapus multiple newline menjadi satu.",
        "clean_toc_label": "Hapus nomor & titik di TOC",
        "clean_toc_help": "Menghapus angka di awal judul daftar isi (misal: '001. Judul' -> 'Judul').",
        "fix_cap_label": "Format Capitalization (Non-Arab)",
        "fix_cap_help": "Mengubah teks non-Arab di TOC menjadi Title Case.",
        "detect_dir_label": "Deteksi arah tulisan (RTL/LTR)",
        "detect_dir_help": "Otomatis menyisipkan karakter kontrol Unicode (RLE/LRE) agar teks rata kanan (Arab) atau kiri (Latin) sesuai dominasi karakter.",
        "filter_header": "Filter Halaman",
        "skip_ids_label": "Skip Page IDs",
        "skip_ids_help": "ID halaman yang ingin dilewati (misal: 1,2,5-10).",
        "max_len_label": "Max Length to Skip",
        "max_len_help": "Lewati halaman jika jumlah karakter melebihi angka ini (0 = nonaktif).",
        "uploader_label": "Pilih file (EPUB, DOCX)",
        "convert_btn": "Konversi Sekarang",
        "processing": "Sedang memproses...",
        "success": "Konversi Berhasil!",
        "download_btn": "📥 Unduh SQLite",
        "error": "Terjadi kesalahan:",
        "guide_title": "📖 Panduan Penggunaan",
        "guide_content": """
### Langkah-langkah Konversi:
1. **Atur Konfigurasi**: Masukkan **Page Marker** jika dokumen Anda menggunakan pemisah halaman manual (misal simbol `@`).
2. **Opsi Pembersihan**: 
    - Gunakan **Hapus baris kosong** untuk merapikan teks yang terlalu renggang.
    - Gunakan **Hapus nomor & titik di TOC** jika daftar isi dokumen Anda memiliki penomoran manual yang ingin dibersihkan.
    - Aktifkan **Deteksi arah tulisan (RTL/LTR)** jika dokumen Anda berisi campuran teks Arab dan Latin.
3. **Unggah File**: Pilih file `.epub` atau `.docx` dari komputer Anda.
4. **Konversi & Unduh**: Klik tombol **Konversi Sekarang**, tunggu proses selesai, lalu klik **Unduh SQLite**.

### Penjelasan Fitur Khusus:
- **Footnote Separator**: Jika Anda memiliki baris pemisah khusus antara teks dan footnote, masukkan di sini agar otomatis diubah menjadi format standar Maktabah (`__________`).
- **Deteksi RTL/LTR**: Fitur ini menyisipkan karakter transparan agar aplikasi Maktabah secara otomatis mengatur rata kanan/kiri.
        """,
        "info_cloud": "Aplikasi ini berjalan tanpa server pribadi menggunakan Streamlit Cloud."
    },
    "en": {
        "title": "📚 E-Book to SQLite Converter",
        "header_desc": "Upload your document files to convert them into SQLite format compatible with the Maktabah application.",
        "config_header": "Configuration Options",
        "page_marker_label": "Page Marker",
        "page_marker_help": "Page separator character (e.g., @). Leave empty if not applicable.",
        "footnote_markers_label": "Footnote Markers",
        "footnote_markers_help": "Footnote prefix characters, comma-separated.",
        "footnote_sep_label": "Footnote Separator",
        "footnote_sep_help": "Footnote separator character (e.g., ---). Will be changed to '__________' if the line contains only this character.",
        "parts_label": "Parts Definition",
        "parts_help": "Format: start_id:part_num,...",
        "cleaning_header": "Cleaning Options",
        "collapse_newlines_label": "Collapse extra newlines",
        "collapse_newlines_help": "Removes multiple newlines into a single one.",
        "clean_toc_label": "Clean numbers & dots in TOC",
        "clean_toc_help": "Removes leading numbers in TOC titles (e.g., '001. Title' -> 'Title').",
        "fix_cap_label": "Format Capitalization (Non-Arab)",
        "fix_cap_help": "Converts non-Arabic TOC text to Title Case.",
        "detect_dir_label": "Detect text direction (RTL/LTR)",
        "detect_dir_help": "Automatically inserts Unicode control characters (RLE/LRE) for right (Arabic) or left (Latin) alignment based on character dominance.",
        "filter_header": "Page Filtering",
        "skip_ids_label": "Skip Page IDs",
        "skip_ids_help": "Page IDs to skip (e.g., 1,2,5-10).",
        "max_len_label": "Max Length to Skip",
        "max_len_help": "Skip page if character count exceeds this number (0 = disabled).",
        "uploader_label": "Choose file (EPUB, DOCX)",
        "convert_btn": "Convert Now",
        "processing": "Processing...",
        "success": "Conversion Successful!",
        "download_btn": "📥 Download SQLite",
        "error": "An error occurred:",
        "guide_title": "📖 Usage Guide",
        "guide_content": """
### Conversion Steps:
1. **Set Configuration**: Enter **Page Marker** if your document uses manual page separators (e.g., `@`).
2. **Cleaning Options**: 
    - Use **Collapse extra newlines** to tidy up text that is too sparse.
    - Use **Clean numbers & dots in TOC** if your TOC has manual numbering to be cleaned.
    - Enable **Detect text direction (RTL/LTR)** if your document contains mixed Arabic and Latin text.
3. **Upload File**: Select an `.epub` or `.docx` file from your computer.
4. **Convert & Download**: Click the **Convert Now** button, wait for completion, then click **Download SQLite**.

### Special Features:
- **Footnote Separator**: If you have a specific separator line between text and footnotes, enter it here to automatically convert it to the standard Maktabah format (`__________`).
- **Detect RTL/LTR**: This feature inserts transparent characters so the Maktabah app automatically handles right/left alignment.
        """,
        "info_cloud": "This application runs without a private server using Streamlit Cloud."
    }
}

st.set_page_config(page_title="Universal E-Book to SQLite Converter", layout="centered")

# --- Language Selection ---
lang = st.sidebar.selectbox("Language / Bahasa", options=["id", "en"], format_func=lambda x: "Bahasa Indonesia" if x == "id" else "English")
t = TEXTS[lang]

st.title(t["title"])
st.markdown(t["header_desc"])

# --- Sidebar for Options ---
st.sidebar.header(t["config_header"])
page_marker = st.sidebar.text_input(t["page_marker_label"], value="", help=t["page_marker_help"])
footnote_markers = st.sidebar.text_input(t["footnote_markers_label"], value="¬,(¬", help=t["footnote_markers_help"])
footnote_sep = st.sidebar.text_input(t["footnote_sep_label"], value="", help=t["footnote_sep_help"])
parts_spec = st.sidebar.text_area(t["parts_label"], value="", placeholder="1:1,747:2", help=t["parts_help"])

st.sidebar.divider()
st.sidebar.header(t["cleaning_header"])
collapse_newlines = st.sidebar.checkbox(t["collapse_newlines_label"], value=True, help=t["collapse_newlines_help"])
clean_toc = st.sidebar.checkbox(t["clean_toc_label"], value=False, help=t["clean_toc_help"])
fix_cap = st.sidebar.checkbox(t["fix_cap_label"], value=False, help=t["fix_cap_help"])
detect_dir = st.sidebar.checkbox(t["detect_dir_label"], value=False, help=t["detect_dir_help"])

st.sidebar.divider()
st.sidebar.header(t["filter_header"])
skip_ids = st.sidebar.text_input(t["skip_ids_label"], value="", help=t["skip_ids_help"])
max_len_skip = st.sidebar.number_input(t["max_len_label"], value=0, help=t["max_len_help"])

# --- File Uploader ---
uploaded_file = st.file_uploader(t["uploader_label"], type=["epub", "docx"])

if uploaded_file is not None:
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    if st.button(t["convert_btn"]):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(percent, text):
            progress_bar.progress(percent)
            status_text.text(text)

        with st.spinner(t["processing"]):
            try:
                # 1. Save uploaded file to temp
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_input:
                    tmp_input.write(uploaded_file.getvalue())
                    input_path = tmp_input.name

                # 2. Prepare output path
                output_filename = os.path.splitext(uploaded_file.name)[0] + ".sqlite"
                output_path = os.path.join(tempfile.gettempdir(), output_filename)

                # 3. Run conversion
                success = False
                options = {
                    "book_id": "00000",
                    "page_marker": page_marker if page_marker else None,
                    "footnote_markers_str": footnote_markers,
                    "footnote_separator": footnote_sep if footnote_sep else None,
                    "parts_str": parts_spec,
                    "collapse_newlines": collapse_newlines,
                    "clean_toc": clean_toc,
                    "fix_cap": fix_cap,
                    "detect_dir": detect_dir,
                    "skip_ids_str": skip_ids,
                    "max_len_skip": max_len_skip,
                    "progress_callback": update_progress
                }

                if file_extension == ".epub":
                    success = process_epub(input_path, output_path, **options)
                elif file_extension == ".docx":
                    success = process_docx(input_path, output_path, **options)
                else:
                    st.error(f"Format {file_extension} not supported.")

                update_progress(1.0, "Done!" if lang == "en" else "Selesai!")

                # 4. Download button
                if success:
                    st.success(t["success"])
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label=t["download_btn"],
                            data=f,
                            file_name=output_filename,
                            mime="application/x-sqlite3"
                        )
                
                if os.path.exists(input_path): os.remove(input_path)

            except Exception as e:
                st.error(f"{t['error']} {e}")
                st.exception(e)

st.divider()
st.divider()

with st.expander(t["guide_title"]):
    st.markdown(t["guide_content"])

st.info(t["info_cloud"])
