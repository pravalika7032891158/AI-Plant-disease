import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time
import pandas as pd
from gtts import gTTS
import tempfile

# ---------------- CONFIGURATION ----------------
st.set_page_config(page_title="🌿 AI Plant Disease Identifier", page_icon="🌱", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# ---------------- THEME TOGGLE ----------------
if "theme" not in st.session_state:
    st.session_state.theme = "light"  # Default light theme

def apply_theme(theme):
    if theme == "light":
        bg, text, card, accent, border = "#f6fff8", "#1a202c", "#ffffff", "#2f855a", "#c6f6d5"
    else:
        bg, text, card, accent, border = "#0b1220", "#f0fff4", "#132a13", "#38a169", "#22543d"
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {bg};
            color: {text};
        }}
        .main-card {{
            background: {card};
            padding: 2rem;
            border-radius: 20px;
            border: 1px solid {border};
            box-shadow: 0px 8px 24px rgba(0,0,0,0.15);
        }}
        .btn-primary button {{
            background: {accent} !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
        }}
        h1, h2, h3, h4 {{ color: {accent}; }}
        </style>
    """, unsafe_allow_html=True)

# Sidebar theme switch
with st.sidebar:
    st.markdown("### 🌗 Appearance")
    dark_toggle = st.toggle("Dark Mode", value=(st.session_state.theme == "dark"))
    st.session_state.theme = "dark" if dark_toggle else "light"
    apply_theme(st.session_state.theme)

# ---------------- TITLE ----------------
st.markdown(
    """
    <div style='text-align:center; padding:1.5rem; border-radius:15px; background:rgba(56,178,172,0.1);'>
        <h1>🌿 AI-Based Plant Disease Identification System</h1>
        <p>A camera in every hand can now protect every plant!</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------- SESSION STATE ----------------
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = ""
if "camera_active" not in st.session_state:
    st.session_state.camera_active = False
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "reset_triggered" not in st.session_state:
    st.session_state.reset_triggered = False

# ---------------- HOW IT WORKS ----------------
with st.expander("🧩 How It Works"):
    st.markdown("""
    1️⃣ Upload or capture a leaf image  
    2️⃣ AI analyzes the image and detects disease  
    3️⃣ Get detailed report + remedies + prevention tips  
    4️⃣ Listen to the voice summary in your selected language 🎧  
    5️⃣ Ask follow-up questions using the AI Agribot below  
    """)

# ---------------- IMAGE INPUT ----------------
st.markdown("<div class='main-card'>", unsafe_allow_html=True)
st.header("📸 Upload or Capture Leaf Image")

# 🌐 Language selector
language = st.selectbox(
    "🌍 Select Output Language",
    ["English", "Telugu", "Hindi", "Tamil"],
    index=0
)

uploaded_file = st.file_uploader(
    "Upload a clear image of the affected leaf",
    type=["jpg", "jpeg", "png"],
    key=f"uploader_{st.session_state.uploader_key}",
)

if st.button("📷 Take Photo"):
    st.session_state.camera_active = not st.session_state.camera_active

if st.session_state.camera_active:
    st.info("Click the *round capture button* below to take a photo.")
    camera_input = st.camera_input("Capture image here")
    if camera_input is not None:
        uploaded_file = None
        st.session_state.uploaded_image = Image.open(camera_input)
        st.session_state.camera_active = False
else:
    camera_input = None

if uploaded_file is not None:
    st.session_state.uploaded_image = Image.open(uploaded_file)

# ---------------- IMAGE DISPLAY & ANALYSIS ----------------
if st.session_state.uploaded_image is not None:
    st.image(st.session_state.uploaded_image, caption="Uploaded Image", use_container_width=True)
    st.success("✅ Image loaded successfully")

    if st.button("🔍 Identify Disease & Get Analysis", key="analyze_btn"):
        with st.spinner("Analyzing the leaf... Please wait ⏳"):
            try:
                img_byte_arr = io.BytesIO()
                st.session_state.uploaded_image.save(img_byte_arr, format="PNG")
                img_bytes = img_byte_arr.getvalue()

                prompt = f"""
                You are an expert agricultural AI assistant.
                Analyze the given leaf image and identify:
                1. The plant name
                2. Disease Name
                3. Cause/Pathogen
                4. Symptoms
                5. Severity Level (Low/Medium/High)
                6. Precautions
                7. Treatments (organic & chemical)
                8. Impact on yield or quality
                9. Future preventive measures

                Format the response in a structured and visually clear way.
                Respond in {language}.
                """

                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content([
                    prompt,
                    {"mime_type": "image/png", "data": img_bytes}
                ])

                st.session_state.analysis_result = response.text
                st.subheader("🌾 Disease Detection & Analysis Report")
                st.markdown(f"<div class='main-card'>{st.session_state.analysis_result}</div>", unsafe_allow_html=True)

                # 🎧 VOICE OUTPUT FEATURE (Multilingual)
                if st.session_state.analysis_result:
                    with st.spinner("Generating voice output... 🎧"):
                        try:
                            lang_map = {
                                "English": "en",
                                "Telugu": "te",
                                "Hindi": "hi",
                                "Tamil": "ta"
                            }
                            selected_lang = lang_map.get(language, "en")
                            tts = gTTS(text=st.session_state.analysis_result, lang=selected_lang)
                            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                            tts.save(temp_file.name)
                            st.success(f"🔊 Voice output generated in {language}!")
                            st.audio(temp_file.name, format="audio/mp3")
                        except Exception as e:
                            st.error(f"⚠ Voice generation error: {e}")

                # 📥 Download Report
                st.download_button(
                    label="📥 Download Report",
                    data=st.session_state.analysis_result,
                    file_name="plant_disease_analysis.txt",
                    mime="text/plain",
                )

                # 📊 Visualization Dashboard
                st.markdown("### 📊 Confidence Visualization (Sample Representation)")
                data = pd.DataFrame({
                    "Disease": ["Leaf Spot", "Blight", "Rust", "Healthy"],
                    "Confidence (%)": [40, 35, 15, 10]
                })
                data = data.set_index("Disease")
                st.bar_chart(data, height=250, color="#2f855a")

            except Exception as e:
                st.error(f"⚠ Error: {e}")

st.markdown("</div>", unsafe_allow_html=True)

# ---------------- RESET FUNCTION ----------------
def trigger_reset():
    st.session_state.reset_triggered = True

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
st.button("🔄 Reset", on_click=trigger_reset)
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.reset_triggered:
    time.sleep(0.2)
    uploader_key = st.session_state.get("uploader_key", 0) + 1
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state["uploader_key"] = uploader_key
    st.rerun()

# ---------------- AI AGRIBOT CHAT ----------------
st.markdown("---")
st.subheader("🤖 Ask the AI Agribot")

query = st.text_input("Type your farming or plant health question:")
if query:
    with st.spinner("Thinking... 🌱"):
        try:
            chat_model = genai.GenerativeModel("gemini-2.0-flash")
            answer = chat_model.generate_content(query)
            st.markdown(f"*AI Agribot:* {answer.text}")
        except Exception as e:
            st.error(f"⚠ Chatbot error: {e}")

# ---------------- ENHANCED PROFESSIONAL FOOTER ----------------

footer_html = """
<style>
.footer {
    background: linear-gradient(135deg, #1f4037 0%, #99f2c8 100%);
    color: white;
    padding: 3rem 2rem 2rem 2rem;
    border-radius: 25px 25px 0 0;
    margin-top: 3rem;
    box-shadow: 0px -5px 25px rgba(0, 0, 0, 0.2);
    font-family: 'Segoe UI', sans-serif;
}
.footer h3 {
    color: #f6fff8;
    font-weight: bold;
    font-size: 20px;
    margin-bottom: 0.5rem;
    text-shadow: 0 0 10px rgba(255,255,255,0.2);
}
.footer p {
    color: #e7f9ee;
    font-size: 15px;
    line-height: 1.6;
}
.footer a {
    color: #ffffff;
    text-decoration: none;
    transition: all 0.3s ease-in-out;
}
.footer a:hover {
    color: #1f4037;
    background: #ffffff;
    padding: 2px 6px;
    border-radius: 5px;
}
.footer-container {
    display: flex;
    justify-content: space-evenly;
    flex-wrap: wrap;
    gap: 3rem;
    text-align: left;
}
.footer-divider {
    width: 80%;
    margin: 2rem auto 1rem auto;
    border-top: 1px solid rgba(255, 255, 255, 0.4);
}
.footer-bottom {
    text-align: center;
    font-size: 15px;
    opacity: 0.95;
    padding-top: 0.8rem;
    font-weight: 500;
}
.footer-heart {
    color: #ff6b6b;
    animation: heartbeat 1.5s infinite;
}
@keyframes heartbeat {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.3); }
}
</style>

<div class="footer">
    <div class="footer-container">
        <div>
            <h3>🌿 About Us</h3>
            <p>
                We are <b>Tech Busters</b> — a passionate team dedicated to using Artificial Intelligence 
                to empower farmers, protect crops, and create sustainable agri-tech solutions for the future.
            </p>
        </div>

        <div>
            <h3>📬 Contact Us</h3>
            <p>Email: <a href="mailto:techbusters.ai@gmail.com">techbusters.ai@gmail.com</a></p>
            <p>Phone: <a href="tel:+91XXXXXXXXXX">+91 XXXXX XXXXX</a></p>
            <p>Website: <a href="#">www.techbusters.ai</a></p>
            <p>Follow us: 
                <a href="#">Instagram</a> • 
                <a href="#">LinkedIn</a> • 
                <a href="#">GitHub</a>
            </p>
        </div>
    </div>

    <div class="footer-divider"></div>

    <div class="footer-bottom">
        🌾 <b>Built with</b> <span class="footer-heart">❤</span> <b>for Farmers</b> | © 2025 <b>Tech Busters</b> — All Rights Reserved.
    </div>
</div>
"""

st.components.v1.html(footer_html, height=480)
