import streamlit as st
import requests
import os
import base64
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
LOGO_PATH = r"C:\Users\Udarsh\.gemini\antigravity\brain\32e4c94e-9dbf-4ddc-8742-a7fd61464518\setu_logo_1785409259763.jpg"

st.set_page_config(page_title="Setu (சேது) Advisory", page_icon="🌾", layout="centered")

# --- Custom Purple Glassmorphism CSS ---
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except:
        return ""

# Background image can be a dark gradient
st.markdown(f"""
<style>
/* Main Background Gradient */
.stApp {{
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    background-attachment: fixed;
    color: #e0e0e0;
}}

/* Hide main menu and footer for clean look */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}

/* Typography */
h1, h2, h3, h4, h5, h6, p, span, div {{
    font-family: 'Inter', 'Roboto', sans-serif !important;
}}
h1, h2, h3 {{
    background: -webkit-linear-gradient(45deg, #b06ab3, #4568dc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
}}

/* Glassmorphism Containers (Inputs, Tabs, Expanders) */
div[data-baseweb="input"] > div, 
div[data-baseweb="select"] > div,
.stTextArea textarea, 
.stFileUploader, 
.stTabs [data-baseweb="tab-list"],
.stExpander {{
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    color: white !important;
}}

/* Buttons */
.stButton > button {{
    background: linear-gradient(90deg, #b06ab3 0%, #4568dc 100%) !important;
    border: none !important;
    border-radius: 25px !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.5rem 2rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(176, 106, 179, 0.4) !important;
}}
.stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(176, 106, 179, 0.6) !important;
}}

/* Success/Error/Warning Messages (Glass style) */
.stSuccess, .stError, .stWarning, .stInfo {{
    background: rgba(255, 255, 255, 0.08) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 15px !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    color: #fff !important;
}}

/* Top header structural padding */
.css-18e3th9 {{
    padding-top: 2rem;
}}
</style>
""", unsafe_allow_html=True)

# --- Header & Logo ---
col1, col2 = st.columns([1, 4])
with col1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=100, use_column_width=False)
with col2:
    st.title("Setu (சேது)")
    st.markdown("### Next-Gen Offline Farm Advisory")

st.markdown("---")

# --- Interface ---
st.markdown("##### Configuration")
language_override = st.selectbox(
    "Language Override:", 
    ["Auto-detect", "English", "Tamil", "Telugu", "Hindi"],
    help="Force a specific language if auto-detection fails."
)

st.markdown("---")

tab1, tab2 = st.tabs(["💬 Chat", "📸 Visual & Audio"])

with tab1:
    st.markdown("### Ask a Question")
    user_query = st.text_input("Enter your query (English, Tamil, Telugu, Hindi, or Code-switched):", placeholder="e.g. How to treat late blight in potatoes?")
    
    col_btn, _ = st.columns([1, 5])
    with col_btn:
        ask_btn = st.button("Ask Assistant")
        
    if ask_btn:
        if user_query:
            with st.spinner("Analyzing..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/chat", 
                        data={"text": user_query, "language_override": language_override}
                    )
                    if response.status_code == 200:
                        st.success("Response Generated:")
                        st.write(response.json().get("response", "No response returned."))
                    else:
                        st.error(f"Error connecting to backend: {response.text}")
                except Exception as e:
                    st.error(f"Failed to connect to backend API: {e}")
        else:
            st.warning("Please enter a query.")

with tab2:
    st.markdown("### Multimodal Input")
    st.info("Take a photo of a crop or pest, or upload an audio question.")
    
    camera_image = st.camera_input("Take a picture")
    
    with st.expander("📁 Upload Files Instead"):
        image_file = st.file_uploader("Upload leaf/crop image", type=["jpg", "jpeg", "png"])
        st.markdown("*Note: Use `.wav` for optimal offline processing.*")
        audio_file = st.file_uploader("Upload audio recording", type=["wav", "mp3", "m4a"])
    
    final_image = camera_image if camera_image else image_file
    
    if st.button("Process Multimodal Input"):
        if audio_file or final_image:
            with st.spinner("Processing Media..."):
                files = {}
                data = {"language_override": language_override}
                if audio_file:
                    files["audio"] = (audio_file.name, audio_file.getvalue(), audio_file.type)
                if final_image:
                    files["image"] = (final_image.name, final_image.getvalue(), final_image.type)
                    
                try:
                    response = requests.post(f"{BACKEND_URL}/chat", data=data, files=files)
                    if response.status_code == 200:
                        st.success("Analysis Complete:")
                        st.write(response.json().get("response", "No response returned."))
                    else:
                        st.error(f"Error connecting to backend: {response.text}")
                except Exception as e:
                    st.error(f"Failed to connect to backend API: {e}")
        else:
            st.warning("Please provide a photo or audio file.")
