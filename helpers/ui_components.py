import streamlit as st
import base64
import os

try:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    _BASE_DIR = os.getcwd()

# Shared mapping for school images
SCHOOL_IMAGE_MAP = {
    "NEPS":               "download.png",
    "BGIS":               "bgis.png",
    "CRUISE":             "cruise.jfif",
    "OMEGA":              "omega.jfif",
    "SCHOOL OF TOMORROW": "schoolof.jfif",
    "FUTURE":             "future.jfif",
    "SOUTH WEST":         "south_west.jfif",
    "STANDFORD":          "standford.png",
}

def get_base64_image(image_path):
    try:
        if not os.path.exists(image_path):
            return ""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

def get_school_logo_b64(school_name: str) -> str:
    filename = SCHOOL_IMAGE_MAP.get(school_name.upper(), "")
    if not filename: return ""
    return get_base64_image(os.path.join(_BASE_DIR, filename))

def inject_school_card_css():
    """Injects the CSS needed to make the entire school card clickable."""
    st.markdown("""
    <style>
    /* Target the st.container() inner block */
    div[data-testid="stVerticalBlock"]:has(> div.element-container .custom-school-card) {
        position: relative !important;
        border: 1px solid rgba(203,213,225,0.7) !important;
        border-radius: 14px !important;
        padding: 16px 12px 12px !important;
        background: #ffffff !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.04) !important;
        height: 100% !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div.element-container .custom-school-card):hover {
        border-color: #3b82f6 !important;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1) !important;
        transform: translateY(-2px) !important;
    }
    /* Stretch button over everything seamlessly */
    div[data-testid="stVerticalBlock"]:has(> div.element-container .custom-school-card) .stButton {
        position: absolute !important;
        top: 0 !important; left: 0 !important; bottom: 0 !important; right: 0 !important;
        margin: 0 !important;
        opacity: 0 !important;
        z-index: 10 !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div.element-container .custom-school-card) .stButton button {
        width: 100% !important; height: 100% !important; cursor: pointer !important; padding: 0 !important; margin: 0 !important;
    }

    /* Base styles for the card internals */
    .custom-school-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
    }
    .custom-school-card img {
        height: 55px;
        width: 100%;
        max-width: 140px;
        object-fit: contain;
        margin-bottom: 12px;
        border-radius: 6px;
    }
    .custom-school-card .no-logo {
        height: 55px;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 12px;
        border: 1px dashed rgba(203,213,225,0.8);
        border-radius: 6px;
        color: #94a3b8;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        background: rgba(248,250,252,0.5);
    }
    .custom-school-title {
        font-size: 14px;
        font-weight: 700;
        color: #1e293b;
        text-align: center;
        line-height: 1.3;
    }
    </style>
    """, unsafe_allow_html=True)

def render_clickable_school_card(school_name, key=None):
    """
    Renders a visually appealing school card with logo and name.
    Returns True if clicked.
    """
    logo_b64 = get_school_logo_b64(school_name)
    btn_key = key if key else f"btn_card_{school_name}"
    
    # We use a container to wrap both the visual and the overlay button
    # The CSS uses :has(> div.element-container .custom-school-card) 
    # to target exactly this returned container block.
    with st.container():
        img_html = f'<img src="data:image/jpeg;base64,{logo_b64}"/>' if logo_b64 else '<div class="no-logo">No Logo</div>'
        
        st.markdown(f"""
        <div class="custom-school-card">
            {img_html}
            <div class="custom-school-title">{school_name}</div>
        </div>
        """, unsafe_allow_html=True)
        
        clicked = st.button(school_name, key=btn_key, use_container_width=True)
        return clicked
