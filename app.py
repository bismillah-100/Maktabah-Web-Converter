import streamlit as st
import os
import tempfile
from converters.epub import process_epub
from converters.docx import process_docx

st.set_page_config(page_title="Universal E-Book to SQLite Converter", layout="centered")

st.title("📚 E-Book to SQLite Converter")
st.markdown("""
Unggah file dokumen Anda untuk dikonversi menjadi format SQLite yang kompatibel dengan aplikasi Maktabah.
""")

# --- Sidebar for Options ---
st.sidebar.header("Opsi Konfigurasi")
book_id = st.sidebar.text_input("Book ID", value="00000", help="ID unik untuk nama tabel di database.")
page_marker = st.sidebar.text_input("Page Marker", value="", help="Karakter pemisah halaman (misal: @). Kosongkan jika tidak ada.")
footnote_markers = st.sidebar.text_input("Footnote Markers", value="¬,(¬", help="Karakter prefix footnote, dipisah koma.")
parts_spec = st.sidebar.text_area("Parts Definition", value="", placeholder="1:1,747:2", help="Format: start_id:part_num,...")

# --- File Uploader ---
uploaded_file = st.file_uploader("Pilih file (EPUB, DOCX)", type=["epub", "docx"])

if uploaded_file is not None:
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    if st.button("Konversi Sekarang"):
        with st.spinner("Sedang memproses..."):
            try:
                # 1. Simpan file unggahan ke file sementara
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_input:
                    tmp_input.write(uploaded_file.getvalue())
                    input_path = tmp_input.name

                # 2. Siapkan path output sementara
                output_filename = os.path.splitext(uploaded_file.name)[0] + ".sqlite"
                output_path = os.path.join(tempfile.gettempdir(), output_filename)

                # 3. Jalankan konversi berdasarkan format
                success = False
                options = {
                    "book_id": book_id,
                    "page_marker": page_marker if page_marker else None,
                    "footnote_markers_str": footnote_markers,
                    "parts_str": parts_spec
                }

                if file_extension == ".epub":
                    success = process_epub(input_path, output_path, **options)
                elif file_extension == ".docx":
                    success = process_docx(input_path, output_path, **options)
                else:
                    st.error(f"Format {file_extension} belum didukung.")

                # 4. Sajikan hasil unduhan
                if success:
                    st.success("Konversi Berhasil!")
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="📥 Unduh SQLite",
                            data=f,
                            file_name=output_filename,
                            mime="application/x-sqlite3"
                        )
                
                # Bersihkan file sementara
                if os.path.exists(input_path): os.remove(input_path)
                # Note: output_path biarkan dulu sampai user klik download (atau akan dihapus otomatis oleh sistem temp OS nanti)

            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
                st.exception(e)

st.divider()
st.info("Aplikasi ini berjalan tanpa server pribadi menggunakan Streamlit Cloud.")
