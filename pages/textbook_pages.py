import json
import importlib.util
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).parent.parent
module_path = PROJECT_ROOT / "models" / "textbook.py"
spec = importlib.util.spec_from_file_location(
    "_streamlit_practice_textbook_model", module_path
)
if spec is None or spec.loader is None:
    raise ImportError(f"教科書モデルを読み込めませんでした：{module_path}")
textbook_model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(textbook_model)
add_comment = textbook_model.add_comment
add_textbook = textbook_model.add_textbook
like_comment = textbook_model.like_comment
load_textbooks = textbook_model.load_textbooks


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
        department = st.text_input(
            "学科（必須）",
            placeholder="例：情報工学EP",
        )
        lecture_name = st.text_input(
            "授業名（必須）",
            placeholder="例：線形代数学",
        )
        professor_name = st.text_input(
            "教授名（必須）",
            placeholder="例：山田 太郎",
        )

        col1, col2 = st.columns(2)
        with col1:
            required_textbook = st.text_input(
                "指定教科書名（必須）",
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
                    department=department,
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

    departments = sorted(
        {item["department"] or "学科未登録" for item in textbooks}
    )
    selected_department = st.selectbox(
        "学科で絞り込む",
        ["すべての学科"] + departments,
    )

    search = st.text_input(
        "学科・講義名・教授名・教科書名で検索",
        placeholder="キーワードを入力",
    )

    if textbooks:
        filtered = [
            item
            for item in textbooks
            if selected_department == "すべての学科"
            or (item["department"] or "学科未登録") == selected_department
        ]
        keyword = search.strip().lower()
        if keyword:
            filtered = [
                item
                for item in textbooks
                if any(
                    keyword in str(item[key]).lower()
                    for key in (
                        "department",
                        "lecture_name",
                        "professor_name",
                        "required_textbook",
                        "reference_book",
                    )
                )
            ]

        st.caption(f"{len(filtered)} 件")
        if filtered:
            for item in filtered:
                department_label = item["department"] or "学科未登録"
                title = (
                    f"{department_label} | {item['lecture_name']} "
                    f"- {item['professor_name']}教授"
                )
                with st.expander(title, expanded=False):
                    st.markdown(f"**学科：** {department_label}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**指定教科書**")
                        st.write(item["required_textbook"] or "未登録")
                    with col2:
                        st.markdown("**市販参考書**")
                        st.write(item["reference_book"] or "未登録")

                    st.divider()
                    st.subheader("レビュー")
                    comments = sorted(
                        item["comments"],
                        key=lambda comment: (-comment["likes"], comment["id"]),
                    )

                    if comments:
                        for comment in comments:
                            comment_container = st.container()
                            comment_container.markdown(comment["text"])
                            vote_key = f"{item['id']}:{comment['id']}"
                            voted = vote_key in st.session_state
                            good_label = f"グッド済 {comment['likes']}" if voted else f"グッド {comment['likes']}"
                            if comment_container.button(
                                good_label,
                                key=f"good-{vote_key}",
                                disabled=voted,
                                use_container_width=False,
                            ):
                                try:
                                    like_comment(item["id"], comment["id"])
                                    st.session_state[vote_key] = True
                                    st.rerun()
                                except (ValueError, OSError) as error:
                                    st.error(str(error))
                            comment_container.caption("役に立った！")
                    else:
                        st.caption("まだレビューはありません")

                    with st.form(key=f"comment-form-{item['id']}", clear_on_submit=True):
                        comment_text = st.text_area(
                            "レビューを書く",
                            placeholder="教科書の使い方、難易度、授業との相性など",
                            key=f"comment-text-{item['id']}",
                        )
                        if st.form_submit_button("レビューを投稿"):
                            try:
                                add_comment(item["id"], comment_text)
                                st.success("レビューを投稿しました")
                                st.rerun()
                            except (ValueError, OSError) as error:
                                st.error(str(error))
        else:
            st.info("該当する教科書情報はありません")
    else:
        st.info("まだ教科書情報が登録されていません")