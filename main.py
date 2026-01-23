import streamlit as st
import os
from PIL import Image
import base64
import io
import json
from openai import OpenAI

# --- 1. Page Configuration & UI Theme ---
st.set_page_config(
    page_title="NutriSnapAI", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize theme in session state
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

# Custom CSS with Dynamic Theme Support
theme_colors = {
    'light': {
        'bg': '#f8f9fa',
        'card_bg': '#ffffff',
        'text': '#1a1a1a',
        'subtext': '#666666',
        'border': '#eef0f2',
        'macro_bg': '#f8f9fa'
    },
    'dark': {
        'bg': '#0e1117',
        'card_bg': '#161b22',
        'text': '#f0f6fc',
        'subtext': '#8b949e',
        'border': '#30363d',
        'macro_bg': '#0d1117'
    }
}

tc = theme_colors[st.session_state.theme]

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    .stApp {{
        background-color: {tc['bg']};
        font-family: 'Inter', sans-serif;
        color: {tc['text']};
    }}

    .main .block-container {{
        max-width: 600px;
        padding-top: 1rem;
    }}

    /* Theme Toggle Button Positioning */
    .theme-toggle-container {{
        position: absolute;
        top: 0;
        right: 0;
        z-index: 1000;
    }}

    .app-card {{
        background-color: {tc['card_bg']};
        border-radius: 24px;
        padding: 32px 24px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.05);
        border: 1px solid {tc['border']};
        text-align: center;
    }}

    .logo-text {{
        font-weight: 800;
        color: {tc['text']};
        letter-spacing: -1px;
        font-size: clamp(2.5rem, 8vw, 3.8rem);
    }}
    .logo-text span {{ color: #8eb384; }}

    .app-title {{
        font-size: 1.6rem;
        font-weight: 800;
        color: {tc['text']};
        margin-bottom: 8px;
    }}
    .app-subtitle {{
        font-size: 0.95rem;
        color: {tc['subtext']};
        margin-bottom: 32px;
    }}

    /* Snap Button Styling */
    .stButton>button {{
        width: 100%;
        height: 52px;
        border-radius: 12px;
        background-color: #d9ead3 !important;
        color: #000000 !important;
        font-weight: 700;
        font-size: 1rem;
        border: 1px solid rgba(0,0,0,0.1);
        transition: all 0.2s;
        margin-top: 16px;
    }}

    .macro-row {{
        display: flex;
        justify-content: space-between;
        background-color: {tc['macro_bg']};
        border-radius: 16px;
        padding: 15px;
        margin-bottom: 20px;
        border: 1px solid {tc['border']};
    }}
    .macro-val {{
        font-size: 1.2rem;
        font-weight: 800;
        color: {tc['text']};
    }}

    .report-box {{
        background-color: #f0f7f0;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 20px;
        border: 1px solid #d9ead3;
        color: #000000 !important;
        font-size: 0.9rem;
        font-style: italic;
    }}

    .health-score-pill {{
        display: inline-block;
        background: #d9ead3;
        color: #000000;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        margin-bottom: 12px;
        border: 1px solid rgba(0,0,0,0.1);
    }}

    /* Hide default elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    [data-testid="stCameraInput"] {{
        border: 2px dashed {tc['border']};
        border-radius: 16px;
        padding: 8px;
    }}

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {tc['macro_bg']};
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {tc['subtext']};
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {tc['card_bg']} !important;
        color: {tc['text']} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. Configuration & Logic ---
AI_INTEGRATIONS_OPENROUTER_API_KEY = os.environ.get("AI_INTEGRATIONS_OPENROUTER_API_KEY")
AI_INTEGRATIONS_OPENROUTER_BASE_URL = os.environ.get("AI_INTEGRATIONS_OPENROUTER_BASE_URL")

def process_image_fast(image_file):
    img = Image.open(image_file)
    img.thumbnail((800, 800))
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

if 'page' not in st.session_state:
    st.session_state.page = 'input'
if 'data' not in st.session_state:
    st.session_state.data = None

# --- 3. UI Layout ---

# Top Row with Toggle
col_logo, col_toggle = st.columns([0.9, 0.1])
with col_toggle:
    st.button("🌙" if st.session_state.theme == 'light' else "☀️", on_click=toggle_theme)

with col_logo:
    st.markdown(f"""
        <div class="logo-container" style="display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 32px; margin-left: 10%;">
            <svg style="width: clamp(40px, 10vw, 60px); height: clamp(40px, 10vw, 60px);" viewBox="0 0 24 24" fill="none" stroke="#8eb384" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 3.5 1.9 9.2A7 7 0 0 1 11 20z"></path><path d="M11 13a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"></path><path d="M11 20v-7"></path></svg>
            <div class="logo-text">Nutri<span>SnapAI</span></div>
        </div>
    """, unsafe_allow_html=True)

if st.session_state.page == 'input':
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="app-title">Snap Your Meal</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Get an instant nutritional analysis of your food.</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📷 Take Photo", "📤 Upload"])

    image_to_process = None

    with tab1:
        camera_photo = st.camera_input("SNAP", key="camera_widget", label_visibility="collapsed")
        if camera_photo:
            image_to_process = camera_photo

    with tab2:
        gallery_photo = st.file_uploader("Browse files", type=["jpg", "jpeg", "png"], key="gallery_widget")
        if gallery_photo:
            image_to_process = gallery_photo

    if image_to_process:
        if st.button("Snap Photo"):
            if not AI_INTEGRATIONS_OPENROUTER_API_KEY:
                st.error("API Error: Missing credentials.")
                st.stop()

            try:
                with st.spinner("Analyzing..."):
                    base64_image = process_image_fast(image_to_process)
                    prompt = (
                        "Analyze this food image. Provide a JSON object with: "
                        "name, health_score (0-100), calories, protein, carbs, fats, ingredients (list), health_summary, "
                        "short_report (a very concise 1-sentence summary of the food's health impact)."
                    )

                    client = OpenAI(
                        api_key=AI_INTEGRATIONS_OPENROUTER_API_KEY,
                        base_url=AI_INTEGRATIONS_OPENROUTER_BASE_URL
                    )

                    response = client.chat.completions.create(
                        model="google/gemini-2.0-flash-001",
                        messages=[{"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]}],
                        response_format={ "type": "json_object" },
                        temperature=0.1
                    )

                    data = json.loads(response.choices[0].message.content)
                    if isinstance(data, list): data = data[0]
                    st.session_state.data = data
                    st.session_state.page = 'results'
                    st.rerun()

            except Exception as e:
                st.error(f"Analysis failed. Please try again.")
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == 'results':
    data = st.session_state.data
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="app-title">{data.get("name", "Meal Analysis")}</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="report-box">
        {data.get("short_report", "Analyzing impact...")}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="health-score-pill">HEALTH SCORE: {data.get("health_score", 0)}/100</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="macro-row">
        <div class="macro-box">
            <div style="font-size: 0.75rem; font-weight: 600; opacity: 0.7; text-transform: uppercase;">Calories</div>
            <div class="macro-val">{data.get("calories", 0)}</div>
        </div>
        <div class="macro-box">
            <div style="font-size: 0.75rem; font-weight: 600; opacity: 0.7; text-transform: uppercase;">Protein</div>
            <div class="macro-val">{data.get("protein", 0)}g</div>
        </div>
        <div class="macro-box">
            <div style="font-size: 0.75rem; font-weight: 600; opacity: 0.7; text-transform: uppercase;">Carbs</div>
            <div class="macro-val">{data.get("carbs", 0)}g</div>
        </div>
        <div class="macro-box">
            <div style="font-size: 0.75rem; font-weight: 600; opacity: 0.7; text-transform: uppercase;">Fats</div>
            <div class="macro-val">{data.get("fats", 0)}g</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="text-align: left; background: rgba(128, 128, 128, 0.03); border-radius: 16px; padding: 20px; border: 1px solid {tc['border']}; margin-top: 16px;">
        <b>Ingredients:</b><br>{', '.join(data.get('ingredients', []))}<br><br>
        <b>AI Analysis:</b><br>{data.get('health_summary', '')}
    </div>
    """, unsafe_allow_html=True)

    if st.button("Snap Another Meal"):
        st.session_state.page = 'input'
        st.session_state.data = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
