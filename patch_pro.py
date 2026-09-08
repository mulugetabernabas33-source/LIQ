import re

with open('c:/Users/mulug/OneDrive/Desktop/end/pro/pro.py', 'r', encoding='utf-8') as f:
    content = f.read()

show_role_new = '''def show_role():
    render_form_header("Dashboard Access", "Select a dashboard to view.", chip="Direct Access")
    
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    cols = st.columns(3)
    
    dashboards = [
        ("Teacher's Dashboard", "teacher_dashboard", "teacher"),
        ("Parent's Dashboard", "parent_dashboard", "parent"),
        ("School Admin Dashboard", "school_admin_dashboard", "admin"),
        ("Wereda Dashboard", "wereda_dashboard", "wereda"),
        ("Kifle Ketema Dashboard", "kifle_ketema_dashboard", "kk"),
        ("Addis Ababa Dashboard", "addis_ababa_dashboard", "aa"),
        ("System Admin Dashboard", "admin_dashboard", "sysadmin"),
    ]
    
    for idx, (label, route, role_id) in enumerate(dashboards):
        with cols[idx % 3]:
            if st.button(label, use_container_width=True, key=f"btn_{route}"):
                if role_id in ["teacher", "parent"]:
                    st.session_state.logged_in = True
                    st.session_state.user_name = "Demo User"
                    st.session_state.user_role = role_id
                    st.session_state.teacher_id = "demo123"
                    st.session_state.parent_id = "demo123"
                    if role_id == "parent":
                        st.session_state.user_name = "jallel million"
                    elif role_id == "teacher":
                        st.session_state.user_name = "tafesse"
                navigate_to(route)
                
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("Back", use_container_width=True, type="secondary"):
            navigate_to("school")
'''

# Replace show_role block
content = re.sub(r'def show_role\(\):.*?# show register', show_role_new + '\n\n# show register', content, flags=re.DOTALL)

# White UI theme replacements
# Welcome Header
content = content.replace('background-color: #000000;', 'background-color: #ffffff; border-bottom: 1px solid #e2e8f0;')
content = content.replace('color: #ffffff; font-family: \\\'Orbitron\\\', sans-serif;', 'color: #0f172a; font-family: \\\'Orbitron\\\', sans-serif;')
# Sections backgrounds
content = content.replace('background: radial-gradient(circle at center, rgba(30,27,75,0.4) 0%, transparent 70%);', 'background: #ffffff;')
content = content.replace('background: rgba(15,23,42,0.6);', 'background: #f8fafc;')
content = content.replace('background: radial-gradient(circle at bottom, rgba(30,27,75,0.3) 0%, transparent 100%);', 'background: #ffffff;')
# Texts
content = content.replace('color: #ffffff;', 'color: #0f172a;')
content = content.replace('color: white;', 'color: #0f172a;')
content = content.replace('color: #cbd5e1;', 'color: #334155;')
content = content.replace('color: #f8fafc;', 'color: #0f172a;')

# Sidebar backgrounds
content = content.replace('background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%) !important;', 'background: #ffffff !important;')
content = content.replace('background: linear-gradient(180deg, #0f172a 0%, #111827 50%, #0b1120 100%) !important;', 'background: #ffffff !important;')
content = content.replace('[data-testid="stSidebar"] * { color: #e2e8f0 !important; }', '[data-testid="stSidebar"] * { color: #0f172a !important; }')
content = content.replace('[data-testid="stSidebar"] h3 { color: #f8fafc !important;', '[data-testid="stSidebar"] h3 { color: #0f172a !important;')

with open('c:/Users/mulug/OneDrive/Desktop/end/pro/pro.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("pro.py updated successfully.")
