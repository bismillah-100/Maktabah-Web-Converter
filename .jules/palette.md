## 2024-06-25 - Improve CTA Button Visibility in Streamlit
**Learning:** In Streamlit applications, default buttons can blend in with the rest of the UI, making primary call-to-action elements like "Convert" or "Download" less obvious. Applying `type="primary"` and `use_container_width=True` significantly improves their visual prominence, creating larger touch targets and clearer focal points for users.
**Action:** When building or modifying Streamlit interfaces, always ensure that the primary action on the page uses `type="primary"` and is sized appropriately (e.g., full width) to guide user interaction clearly.

## 2024-05-18 - Streamlit Inputs Placeholder Pattern
**Learning:** Adding `placeholder` values to Streamlit `st.text_input` and `st.text_area` provides excellent immediate zero-state guidance without users needing to hover over help tooltips. Setting `page_icon` in `st.set_page_config` is a quick way to improve the browser tab's visual polish.
**Action:** Always check if text inputs have placeholders, especially when specific formats are expected. Also ensure page configuration has a relevant icon.

## 2024-08-16 - Add Empty States to File Uploaders
**Learning:** Streamlit apps often leave empty spaces when file uploaders haven't received a file yet, making the interface feel bare or confusing.
**Action:** When a file uploader `is None`, show a clear empty state message using `st.info` (with an icon) directing users to upload a file to begin the process. This improves perceived responsiveness and gives users a clear next step.

## 2024-06-25 - Improve CTA Button Discoverability with Disabled States
**Learning:** In Streamlit, hiding primary action buttons (like "Convert") completely when prerequisites are missing can cause confusing layout shifts and reduces discoverability. Users don't know where the primary action will eventually appear.
**Action:** Show primary action buttons with `disabled=True` and a helpful `help="..."` tooltip explaining the prerequisite (e.g., "Please upload a file") rather than omitting the `st.button` call entirely. This provides better spatial consistency and clearer guidance.

## 2024-11-20 - Prevent Streamlit Download Button Disappearance
**Learning:** In Streamlit, nesting `st.download_button` inside a conditional block triggered by `st.button()` causes the download button to disappear immediately upon click. This happens because clicking the download button triggers a script rerun, resetting the parent button's state to `False`.
**Action:** When creating a download button that appears after a process triggered by `st.button()`, store the process completion status and necessary data (like file paths) in `st.session_state`. Then, conditionally render the `st.download_button` outside the `st.button()` block based on the session state.

## 2024-11-20 - Progressive Disclosure in Streamlit Sidebars
**Learning:** Displaying too many configuration options at once in a Streamlit sidebar can overwhelm users and cause visual clutter, especially when many options are only needed for advanced use cases.
**Action:** Use `st.sidebar.expander` to group related configuration inputs. Keep the most common or critical configurations expanded by default, and collapse the more advanced options. This progressive disclosure makes the UI cleaner and less intimidating while still providing necessary functionality.

## 2026-07-04 - Enhance Selectbox with Emojis
**Learning:** Adding Unicode icons or country flags within the format_func and label of text-only selectboxes provides immediate visual context and improves user scannability without requiring custom CSS.
**Action:** Apply this pattern to standardized items (like languages or countries) in Streamlit applications.

## 2024-06-20 - Consolidating Streamlit Progress Bar Elements
**Learning:** Using `st.empty()` alongside `st.progress()` to show loading text can cause jarring layout shifts when elements populate, creating a disconnected loading state.
**Action:** Always use the native `text` parameter in `st.progress(..., text="...")` to visually couple the loading bar with its status text and prevent unnecessary DOM repaints/layout shifting.
## 2024-07-11 - Unicode Icons as Visual Anchors
**Learning:** Adding Unicode icons to expander headers (⚙️, 🧹, 🔍) and call-to-action buttons (⚡, 📂) provides immediate visual anchors in text-heavy settings menus and improves scannability. This is a lightweight way to enhance UI structure without needing custom CSS or complex component changes.
**Action:** Consistently use relevant Unicode icons as visual grouping markers in Streamlit sidebars, forms, and primary buttons to improve progressive disclosure and interaction cues.
## 2025-02-18 - Prevent Stale State Artifact Downloads
**Learning:** In Streamlit applications, user inputs and action triggers (like 'Convert') are often decoupled. If a user modifies configuration settings after successfully generating an artifact but before downloading it, they may unknowingly download a stale file that doesn't reflect their latest settings.
**Action:** Always capture the state of configuration inputs upon successful task completion in `st.session_state`. Before rendering a download button for the resulting artifact, compare the current input state against the saved state and display a clear warning (`st.warning`) if they diverge, advising the user to run the process again.
