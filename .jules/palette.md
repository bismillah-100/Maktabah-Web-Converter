## 2024-06-20 - Consolidating Streamlit Progress Bar Elements
**Learning:** Using `st.empty()` alongside `st.progress()` to show loading text can cause jarring layout shifts when elements populate, creating a disconnected loading state.
**Action:** Always use the native `text` parameter in `st.progress(..., text="...")` to visually couple the loading bar with its status text and prevent unnecessary DOM repaints/layout shifting.
