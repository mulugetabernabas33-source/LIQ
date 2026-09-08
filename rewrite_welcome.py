import re

with open('c:/Users/mulug/OneDrive/Desktop/end/pro/pro.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_welcome = '''def show_welcome():
    logo_path = os.path.join(BASE_DIR, "assets", "liq_logo.png")
    logo_base64 = get_base64_image(logo_path)
    logo_html_loading = f'<img src="data:image/png;base64,{logo_base64}" style="width: 150px; animation: pulse 2s infinite;">'
    logo_html_main = f'<img src="data:image/png;base64,{logo_base64}" style="width: 250px; margin-bottom: 20px;">'

    st.markdown(f"""
    <style>
    /* Reset and Global White Theme */
    html, body, [data-testid="stAppViewContainer"], .main {{ 
        background: #ffffff !important; 
        color: #0f172a !important; 
        scroll-behavior: smooth !important; 
    }}
    
    /* Loading Screen */
    .loading-screen {{
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-color: #ffffff;
        z-index: 9999999;
        display: flex;
        justify-content: center;
        align-items: center;
        animation: fadeOut 0.8s ease forwards;
        animation-delay: 2s;
        pointer-events: none;
    }}
    
    @keyframes fadeOut {{
        0% {{ opacity: 1; pointer-events: all; }}
        99% {{ opacity: 0; pointer-events: all; }}
        100% {{ opacity: 0; pointer-events: none; display: none; }}
    }}
    
    @keyframes pulse {{
        0% {{ transform: scale(0.9); opacity: 0.7; }}
        50% {{ transform: scale(1.1); opacity: 1; }}
        100% {{ transform: scale(0.9); opacity: 0.7; }}
    }}

    /* Main Welcome Container */
    .welcome-container {{ 
        width: 100%; 
        display: flex; 
        flex-direction: column; 
        align-items: center; 
        text-align: center;
        padding-top: 120px;
    }}
    
    .home-title {{ 
        font-family: 'Orbitron', sans-serif; 
        font-size: 70px; 
        font-weight: 900; 
        color: #0f172a; 
        letter-spacing: 4px; 
        margin-bottom: 10px;
    }}
    
    .home-subtitle {{
        font-size: 22px; 
        color: #64748b; 
        font-weight: 500; 
        letter-spacing: 1px;
        margin-bottom: 70px;
    }}

    /* Professional Button */
    div.stButton > button {{ 
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important; 
        border: none !important; 
        border-radius: 16px !important; 
        padding: 24px 60px !important; 
        height: auto !important; 
        font-size: 22px !important; 
        font-weight: 700 !important; 
        text-transform: none !important; 
        color: #ffffff !important; 
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important; 
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.15) !important; 
        width: 100%;
        max-width: 450px;
        margin: 0 auto;
        display: block;
    }}
    
    div.stButton > button:hover {{ 
        transform: translateY(-8px) scale(1.03) !important; 
        box-shadow: 0 25px 40px rgba(15, 23, 42, 0.25) !important; 
        background: linear-gradient(135deg, #334155 0%, #1e293b 100%) !important;
    }}
    
    div.stButton > button:active {{
        transform: translateY(2px) scale(0.98) !important;
        box-shadow: 0 5px 15px rgba(15, 23, 42, 0.2) !important;
    }}
    
    div.stButton > button p {{
        color: #ffffff !important;
        margin: 0 !important;
        font-size: 24px !important;
    }}
    
    /* About Section */
    .about-section {{
        margin-top: 200px;
        max-width: 900px;
        text-align: center;
    }}
    
    .about-title {{
        font-size: 44px;
        font-weight: 900;
        color: #0f172a;
        margin-bottom: 25px;
    }}
    
    .about-text {{
        font-size: 20px;
        line-height: 1.8;
        color: #475569;
        margin-bottom: 120px;
    }}
    
    /* Developer Cards */
    .dev-title {{
        font-size: 38px;
        font-weight: 900;
        color: #0f172a;
        margin-bottom: 50px;
    }}
    
    .dev-cards {{
        display: flex;
        flex-wrap: wrap;
        gap: 24px;
        justify-content: center;
        max-width: 1200px;
        margin-bottom: 120px;
    }}
    
    .dev-card {{
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 40px 30px;
        border-radius: 20px;
        width: 290px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.04);
        transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s ease;
    }}
    
    .dev-card:hover {{
        transform: translateY(-15px);
        box-shadow: 0 30px 60px rgba(0,0,0,0.08);
        border-color: #cbd5e1;
    }}
    
    .dev-name {{
        font-size: 24px;
        font-weight: 900;
        color: #0f172a;
        margin-bottom: 12px;
    }}
    
    .dev-desc {{
        font-size: 16px;
        color: #64748b;
        line-height: 1.5;
    }}
    </style>
    
    <div class="loading-screen">
        {logo_html_loading}
    </div>
    
    <div class="welcome-container">
        {logo_html_main}
        <div class="home-title">LIQ</div>
        <div class="home-subtitle">Smart Learning Analytics and Early Warning System</div>
    </div>
    """, unsafe_allow_html=True)

    _, c2, _ = st.columns([1, 1.5, 1])
    with c2:
        if st.button("GET STARTED", key="get_started_btn"):
            navigate_to("school")

    st.markdown("""
    <div class="welcome-container">
        <div class="about-section">
            <div class="about-title">About</div>
            <div class="about-text">
                Transforming Ethiopian Education Through Digital Innovation.<br><br>Ethiopia's education system stands at a pivotal moment. This platform was developed to bring transparency, efficiency, and data-informed decision-making to every level of the country's educational landscape.
            </div>
            
            <div class="dev-title">Main Developer</div>
            <div class="dev-cards">
                <div class="dev-card" style="width: 500px; max-width: 100%;">
                    <div class="dev-name">Bernabas Mulugeta</div>
                    <div class="dev-desc">Grade 11 Student at New English Private School</div>
                </div>
            </div>
            
            <div class="dev-title">Development Team</div>
            <div class="dev-cards">
                <div class="dev-card">
                    <div class="dev-name">Jallel Million</div>
                    <div class="dev-desc">Grade 11 Student at New English Private School</div>
                </div>
                <div class="dev-card">
                    <div class="dev-name">Barkot Daniel</div>
                    <div class="dev-desc">Grade 11 Student at New English Private School</div>
                </div>
                <div class="dev-card">
                    <div class="dev-name">Eyeole Yirga</div>
                    <div class="dev-desc">Grade 11 Student at New English Private School</div>
                </div>
                <div class="dev-card">
                    <div class="dev-name">Henos</div>
                    <div class="dev-desc">Grade 11 Student at New English Private School</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
'''

content = re.sub(r'def show_welcome\(\):.*?# show region', new_welcome + '\n\n# show region', content, flags=re.DOTALL)

with open('c:/Users/mulug/OneDrive/Desktop/end/pro/pro.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated welcome page")
