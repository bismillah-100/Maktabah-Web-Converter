## 2024-06-25 - Improve CTA Button Visibility in Streamlit
**Learning:** In Streamlit applications, default buttons can blend in with the rest of the UI, making primary call-to-action elements like "Convert" or "Download" less obvious. Applying `type="primary"` and `use_container_width=True` significantly improves their visual prominence, creating larger touch targets and clearer focal points for users.
**Action:** When building or modifying Streamlit interfaces, always ensure that the primary action on the page uses `type="primary"` and is sized appropriately (e.g., full width) to guide user interaction clearly.## 2024-05-18 - Streamlit Inputs Placeholder Pattern
**Learning:** Adding `placeholder` values to Streamlit `st.text_input` and `st.text_area` provides excellent immediate zero-state guidance without users needing to hover over help tooltips. Setting `page_icon` in `st.set_page_config` is a quick way to improve the browser tab's visual polish.
**Action:** Always check if text inputs have placeholders, especially when specific formats are expected. Also ensure page configuration has a relevant icon.
## 2024-08-16 - Add Empty States to File Uploaders
**Learning:** Streamlit apps often leave empty spaces when file uploaders haven't received a file yet, making the interface feel bare or confusing.
**Action:** When a file uploader `is None`, show a clear empty state message using `st.info` (with an icon) directing users to upload a file to begin the process. This improves perceived responsiveness and gives users a clear next step.
## 2024-06-25 - Improve CTA Button Discoverability with Disabled States
**Learning:** In Streamlit, hiding primary action buttons (like "Convert") completely when prerequisites are missing can cause confusing layout shifts and reduces discoverability. Users don't know where the primary action will eventually appear.
**Action:** Show primary action buttons with `disabled=True` and a helpful `help="..."` tooltip explaining the prerequisite (e.g., "Please upload a file") rather than omitting the `st.button` call entirely. This provides better spatial consistency and clearer guidance.
