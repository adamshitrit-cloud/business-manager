import streamlit as st
from database import init_db

st.set_page_config(
    page_title="Business Manager",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

st.markdown("""
<style>
    .alert-box {
        background: #fff3cd;
        border-left: 4px solid #f0a500;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 6px;
    }
    .alert-box.danger {
        background: #fde8e8;
        border-left-color: #e53e3e;
    }
</style>
""", unsafe_allow_html=True)

pages = {
    "📊 Dashboard":    "dashboard",
    "📁 Projects":     "projects",
    "💸 Expenses":     "expenses",
    "💰 Revenues":     "revenues",
    "📅 Cash Flow":    "cashflow",
    "👥 Employees":    "employees",
}

with st.sidebar:
    st.title("📊 Business Manager")
    st.divider()
    choice = st.radio("Navigation", list(pages.keys()), label_visibility="collapsed")

page = pages[choice]

if page == "dashboard":
    from pages.dashboard import render
elif page == "projects":
    from pages.projects import render
elif page == "expenses":
    from pages.expenses import render
elif page == "revenues":
    from pages.revenues import render
elif page == "cashflow":
    from pages.cashflow import render
elif page == "employees":
    from pages.employees import render

render()
