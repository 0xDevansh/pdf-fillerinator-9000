import streamlit as st
import os
import tempfile
from utils.pdf_processor import pdf_to_images, overlay_text, draw_bounding_boxes
from utils.llm_helper import detect_form_fields

st.set_page_config(page_title="PDF Form Filler (LOCAL)", layout="wide")

st.title("🤖 AI PDF Form Filler (Local LLM)")
st.markdown("Upload a PDF, let your Local LLM find the blanks, fill them in, and download the result!")

# Sidebar for Configuration
with st.sidebar:
    st.header("LLM Settings")
    api_base = st.text_input("API Base URL", value="https://openrouter.ai/api/v1", help="URL of the LLM Provider")
    api_key = st.text_input("OpenRouter API Key", type="password", help="Your OpenRouter or provider API Key")
    model_name = st.text_input("Model Name", value="qwen/qwen-2.5-vl-72b-instruct", help="Model ID (e.g., qwen/qwen-2.5-vl-72b-instruct)")
    
    st.info("Using OpenRouter (or compatible) for Qwen-VL.")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if 'form_data' not in st.session_state:
    st.session_state.form_data = {}  # {page_idx: [fields]}

if uploaded_file and api_base:
    # Save uploaded file to temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    # Process button
    if st.button("Analyze PDF"):
        with st.spinner("Converting PDF to images and analyzing with Local LLM..."):
            try:
                images = pdf_to_images(tmp_path)
                st.session_state.form_data = {}
                st.session_state.pdf_path = tmp_path
                
                progress_bar = st.progress(0)
                for i, img in enumerate(images):
                    st.text(f"Processing page {i+1}/{len(images)}...")
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_tmp:
                        img.save(img_tmp.name)
                        img_path = img_tmp.name
                    
                    # Call LLM
                    # Pass path string to helper
                    fields = detect_form_fields(img_path, api_base=api_base, api_key=api_key, model=model_name)
                    
                    st.session_state.form_data[i] = fields
                    progress_bar.progress((i + 1) / len(images))
                    
                    # Clean up img tmp
                    os.unlink(img_path)
                
                st.success("Analysis Complete!")
                
                if not st.session_state.form_data or all(not v for v in st.session_state.form_data.values()):
                    st.warning("No fields were detected. Check your LLM's vision capabilities/response.")

            except Exception as e:
                st.error(f"Error processing PDF: {e}")

    # Display Form
    if st.session_state.get('form_data'):
        st.divider()
        st.subheader("Fill in the Details")
        
        all_user_inputs = [] # Flattened list for overlay function
        
        # Iterate through pages
        for page_idx, fields in st.session_state.form_data.items():
            if not fields:
                st.info(f"No fields detected on page {page_idx + 1}")
                continue
                
            with st.expander(f"Page {page_idx + 1}", expanded=True):
                # Columns: Text Inputs | Image Preview
                col1, col2 = st.columns([1, 1])
                
                with col2:
                    if 'pdf_path' in st.session_state:
                        images = pdf_to_images(st.session_state.pdf_path)
                        if page_idx < len(images):
                            # Draw boxes on the image
                            img_with_boxes = draw_bounding_boxes(images[page_idx], fields)
                            st.image(img_with_boxes, caption=f"Page {page_idx+1} (Detected Fields)", use_column_width=True)
                
                with col1:
                    for j, field in enumerate(fields):
                        label = field.get('label', f"Field {j+1}")
                        default_val = ""
                        user_val = st.text_input(label, key=f"p{page_idx}_f{j}")
                        
                        field['value'] = user_val
                        field['page'] = page_idx
                        all_user_inputs.append(field)

        # Generate Button
        if st.button("Generate Filled PDF"):
            if 'pdf_path' in st.session_state:
                 with st.spinner("Generating PDF..."):
                    output_path = st.session_state.pdf_path.replace(".pdf", "_filled.pdf")
                    final_path = overlay_text(st.session_state.pdf_path, all_user_inputs, output_path)
                    
                    with open(final_path, "rb") as f:
                        st.download_button(
                            label="Download Filled PDF",
                            data=f,
                            file_name="filled_form.pdf",
                            mime="application/pdf"
                        )
            else:
                st.error("Session expired, please re-upload.")
