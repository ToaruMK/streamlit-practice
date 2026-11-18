import streamlit as st

st.set_page_config(
    page_title="横浜国立大学 教科書レビュー",
    page_icon="📚",
    layout="wide",
)

st.title("横浜国立大学 教科書レビュー")
st.write("講義で使う教科書や参考書を、学生同士で共有できるサイトです。")

col1, col2 = st.columns([2, 1])
with col1:
    st.page_link(
        "pages/textbook_pages.py",
        label="教科書レビューを開く",
        icon="📖",
        use_container_width=True,
    )
with col2:
    st.page_link(
        "pages/1_high_and_low_game.py",
        label="High & Low",
        icon="🃏",
        use_container_width=True,
    )
