import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.textbook import add_textbook, load_textbooks


st.set_page_config(
    page_title="横浜国立大学 教科書レビュー",
    page_icon="📚",
    layout="wide",
)

st.title("横浜国立大学 教科書レビュー")
st.caption("講義と教授名を登録し、指定教科書と市販参考書を共有できます")

tab_list, tab_add = st.tabs(["教科書一覧", "教科書を追加"])

with tab_add:
    st.subheader("新しい情報を追加")
    with st.form("textbook_form", clear_on_submit=True):
        lecture_name = st.text_input("講義名", placeholder="例：線形代数学")
        professor_name = st.text_input("教授名", placeholder="例：山田 太郎")

        col1, col2 = st.columns(2)
        with col1:
            required_textbook = st.text_input(
                "指定教科書",
                placeholder="授業で指定された教科書",
            )
        with col2:
            reference_book = st.text_input(
                "市販参考書",
                placeholder="授業で使える参考書",
            )

        submitted = st.form_submit_button("追加する", use_container_width=True)

        if submitted:
            try:
                add_textbook(
                    lecture_name,
                    professor_name,
                    required_textbook,
                    reference_book,
                )
                st.success("教科書情報を追加しました")
                st.rerun()
            except (ValueError, OSError) as error:
                st.error(str(error))

with tab_list:
    try:
        textbooks = load_textbooks()
    except (json.JSONDecodeError, OSError, ValueError) as error:
        textbooks = []
        st.error(f"教科書データを読み込めませんでした：{error}")

    search = st.text_input(
        "講義名・教授名・教科書名で検索",
        placeholder="キーワードを入力",
    )

    if textbooks:
        filtered = textbooks
        keyword = search.strip().lower()
        if keyword:
            filtered = [
                item
                for item in textbooks
                if any(
                    keyword in str(item[key]).lower()
                    for key in (
                        "lecture_name",
                        "professor_name",
                        "required_textbook",
                        "reference_book",
                    )
                )
            ]

        st.caption(f"{len(filtered)} 件")
        if filtered:
            table = pd.DataFrame(
                [
                    {
                        "講義名": item["lecture_name"],
                        "教授名": item["professor_name"],
                        "指定教科書": item["required_textbook"] or "未登録",
                        "市販参考書": item["reference_book"] or "未登録",
                    }
                    for item in filtered
                ]
            )
            st.dataframe(table, use_container_width=True, hide_index=True)
        else:
            st.info("該当する教科書情報はありません")
    else:
        st.info("まだ教科書情報が登録されていません")