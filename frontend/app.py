import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Setu (சேது) Advisory", page_icon="🌾")

st.title("Setu (சேது) — Offline Farm Advisory")
st.markdown("Point a camera at a leaf. Ask a question in English, Tamil, Telugu, or Hindi. Get an answer.")

# Interface
tab1, tab2 = st.tabs(["Text Query", "Multimodal Input"])

st.markdown("### Settings")
language_override = st.selectbox(
    "Language (Optional Override):", 
    ["Auto-detect", "English", "Tamil", "Telugu", "Hindi"],
    help="Force a specific language if auto-detection fails."
)

with tab1:
    st.header("Ask a Question")
    user_query = st.text_input("Enter your query (English, Tamil, Telugu, Hindi, or Code-switched):")
    if st.button("Ask"):
        if user_query:
            try:
                response = requests.post(
                    f"{BACKEND_URL}/chat", 
                    data={"text": user_query, "language_override": language_override}
                )
                if response.status_code == 200:
                    st.success("Response:")
                    st.write(response.json().get("response", "No response returned."))
                else:
                    st.error(f"Error connecting to backend: {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend API: {e}")
        else:
            st.warning("Please enter a query.")

with tab2:
    st.header("Show & Tell")
    st.markdown("Take a photo of a crop or pest, or upload an audio question.")
    
    # Primary visual input
    camera_image = st.camera_input("Take a picture")
    
    # Secondary inputs
    with st.expander("Or upload files instead"):
        image_file = st.file_uploader("Upload leaf/crop image", type=["jpg", "jpeg", "png"])
        st.markdown("*Note: Please use `.wav` for optimal offline processing (enables smart chunking). Other formats bypass chunking.*")
        audio_file = st.file_uploader("Upload audio recording", type=["wav", "mp3", "m4a"])
    
    final_image = camera_image if camera_image else image_file
    
    if st.button("Process Input"):
        if audio_file or final_image:
            files = {}
            data = {"language_override": language_override}
            if audio_file:
                files["audio"] = (audio_file.name, audio_file.getvalue(), audio_file.type)
            if final_image:
                files["image"] = (final_image.name, final_image.getvalue(), final_image.type)
                
            try:
                response = requests.post(f"{BACKEND_URL}/chat", data=data, files=files)
                if response.status_code == 200:
                    st.success("Response:")
                    st.write(response.json().get("response", "No response returned."))
                else:
                    st.error(f"Error connecting to backend: {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend API: {e}")
        else:
            st.warning("Please provide a photo or audio file.")
