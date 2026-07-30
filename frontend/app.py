import streamlit as st
import requests

st.set_page_config(page_title="Setu (சேது) Advisory", page_icon="🌾")

st.title("Setu (சேது) — Offline Farm Advisory")
st.markdown("Point a camera at a leaf. Ask a question in Tamil. Get an answer.")

# Interface
tab1, tab2 = st.tabs(["Text Query", "Audio/Image Upload"])

with tab1:
    st.header("Ask a Question")
    user_query = st.text_input("Enter your query (Tamil/English/Code-switched):")
    if st.button("Ask"):
        if user_query:
            try:
                response = requests.post("http://localhost:8000/chat", data={"text": user_query})
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
    st.header("Multimodal Input")
    st.markdown("Not fully wired to model in mock, but this is where audio/vision input goes.")
    
    audio_file = st.file_uploader("Upload audio recording", type=["wav", "mp3", "m4a"])
    image_file = st.file_uploader("Upload leaf/crop image", type=["jpg", "jpeg", "png"])
    
    if st.button("Process Audio/Image"):
        if audio_file or image_file:
            files = {}
            if audio_file:
                files["audio"] = (audio_file.name, audio_file.getvalue(), audio_file.type)
            if image_file:
                files["image"] = (image_file.name, image_file.getvalue(), image_file.type)
                
            try:
                response = requests.post("http://localhost:8000/chat", files=files)
                if response.status_code == 200:
                    st.success("Response:")
                    st.write(response.json().get("response", "No response returned."))
                else:
                    st.error(f"Error connecting to backend: {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend API: {e}")
        else:
            st.warning("Please upload a file.")
