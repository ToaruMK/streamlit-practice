import html
import json
import importlib.util
import uuid
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
rate_textbook = textbook_model.rate_textbook
rating_summary = textbook_model.rating_summary
update_textbook = textbook_model.update_textbook

DEPARTMENTS = [
    "教育",
    "経済",
    "経営",
    "機械",
    "材料",
    "海洋系",
    "化学・生命",
    "数理",
    "物理",
    "電子情報",
    "情報工学",
    "都市社会共生",
    "建築",
    "都市基盤",
    "環境リスク",
]
GRADES = ["1年", "2年", "3年", "4年"]
RATING_CHOICES = [
    "評価しない",
    "★☆☆☆☆",
    "★★☆☆☆",
    "★★★☆☆",
    "★★★★☆",
    "★★★★★",
]


def _rating_value(choice):
    return RATING_CHOICES.index(choice) if choice != RATING_CHOICES[0] else None


def _render_book_rating(item, book_type, metric, metric_label, voter_id):
    summary = rating_summary(item, metric, book_type)
    average = (
        f"{summary['average']:.1f}"
        if summary["average"] is not None
        else "未評価"
    )
    current_vote = next(
        (
            vote["value"]
            for vote in item["ratings"][metric][book_type]
            if vote["voter_id"] == voter_id
        ),
        None,
    )
    st.markdown(
        f"""
        <div class="book-rating-summary">
            <div class="book-rating-label">{metric_label}</div>
            <div class="book-rating-score">
                <span class="book-rating-star">★</span> {average}<span class="book-rating-out-of"> / 5</span>
            </div>
            <div class="book-rating-count">評価した人数：{summary['count']}人</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key=f"book-rating-{book_type}-{metric}-{item['id']}"):
        with st.form(key=f"book-rating-form-{book_type}-{metric}-{item['id']}"):
            choice = st.selectbox(
                f"{metric_label}を評価",
                RATING_CHOICES,
                index=current_vote or 0,
                key=f"book-rating-choice-{book_type}-{metric}-{item['id']}",
            )
            if st.form_submit_button("保存", use_container_width=True):
                value = _rating_value(choice)
                if value is None:
                    st.info("星を選んでから評価を保存してください")
                else:
                    try:
                        rate_textbook(
                            item["id"],
                            metric,
                            value,
                            voter_id,
                            book_type=book_type,
                        )
                        st.success(f"{metric_label}を保存しました")
                        st.rerun()
                    except (ValueError, OSError) as error:
                        st.error(str(error))


def _render_book_reviews(item, book_type, book_label):
    comments = sorted(
        (
            comment
            for comment in item["comments"]
            if comment["book_type"] == book_type
        ),
        key=lambda comment: (-comment["likes"], comment["id"]),
    )
    with st.expander(
        f"『{book_label}』のレビューを見る・投稿する（{len(comments)}件）",
        expanded=False,
    ):
        if comments:
            for comment in comments:
                comment_col, like_col = st.columns([12, 1])
                with comment_col:
                    st.markdown(comment["text"])
                with like_col:
                    vote_key = f"{item['id']}:{comment['id']}"
                    voted = vote_key in st.session_state
                    if st.button(
                        str(comment["likes"]),
                        icon="👍",
                        key=f"good-{vote_key}",
                        disabled=voted,
                        help="グッド済み" if voted else "このレビューにグッド",
                    ):
                        try:
                            like_comment(item["id"], comment["id"])
                            st.session_state[vote_key] = True
                            st.rerun()
                        except (ValueError, OSError) as error:
                            st.error(str(error))
        else:
            st.caption(f"『{book_label}』のレビューはまだありません")

        st.info(
            "使う頻度（毎回・試験前など）、新品がよいか中古でもよいか、"
            "教科書のわかりやすさを書くと、ほかの学生の参考になります。"
        )
        with st.form(
            key=f"comment-form-{book_type}-{item['id']}",
            clear_on_submit=True,
        ):
            comment_text = st.text_area(
                f"『{book_label}』のレビューを書く",
                placeholder=(
                    "例：毎回の授業で使います。書き込みがなければ中古で十分です。"
                    "説明がわかりやすく、予習にも役立ちました。"
                ),
                key=f"comment-text-{book_type}-{item['id']}",
            )
            if st.form_submit_button("レビューを投稿", use_container_width=True):
                try:
                    add_comment(
                        item["id"],
                        comment_text,
                        book_type=book_type,
                    )
                    st.success(f"『{book_label}』のレビューを投稿しました")
                    st.rerun()
                except (ValueError, OSError) as error:
                    st.error(str(error))


st.set_page_config(
    page_title="横浜国立大学 教科書レビュー",
    page_icon="📚",
    layout="wide",
)

st.title("横浜国立大学 教科書レビュー")
st.caption("講義と教授名を登録し、指定教科書と市販参考書を共有できます")
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f7fbff 0%, #f2fbf5 100%);
        color: #263746;
    }
    section[data-testid="stSidebar"] {
        background: #ffffff;
    }
    section[data-testid="stSidebar"] * {
        color: #263746;
    }
    [data-testid="stWidgetLabel"] p,
    [data-testid="stCaptionContainer"] p,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stTabs"] button[role="tab"] * {
        color: #263746 !important;
    }
    [data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0.72);
    }
    [data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid #cfe0d8;
        border-radius: 12px;
    }
    [data-testid="stExpander"] > details {
        background-color: #ffffff !important;
        border: 1px solid #cfe0d8 !important;
        border-radius: 12px;
        overflow: hidden;
    }
    [data-testid="stExpander"] > details > summary {
        background-color: #f6faf8 !important;
        color: #263746 !important;
    }
    [data-testid="stExpander"] > details > summary *,
    [data-testid="stExpander"] > details > summary [data-testid="stMarkdownContainer"] p {
        color: #263746 !important;
        -webkit-text-fill-color: #263746 !important;
    }
    [data-testid="stExpander"] > details > summary:hover,
    [data-testid="stExpander"] > details > summary:focus-visible {
        background-color: #e3f2eb !important;
        color: #145c42 !important;
        outline: 2px solid #167653;
        outline-offset: -2px;
    }
    [data-testid="stExpander"] > details[open] {
        border-color: #8ebba6 !important;
    }
    [data-testid="stExpander"] > details[open] > summary {
        background-color: #e3f2eb !important;
        border-bottom: 1px solid #cfe0d8;
        color: #145c42 !important;
        font-weight: 700;
    }
    [data-testid="stExpander"] > details[open] > summary *,
    [data-testid="stExpander"] > details[open] > summary [data-testid="stMarkdownContainer"] p {
        color: #145c42 !important;
        -webkit-text-fill-color: #145c42 !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        background-color: #ffffff !important;
        color: #263746 !important;
    }
    [data-testid="stAlertContainer"] {
        background-color: #eaf3ff !important;
        border: 1px solid #9ec5fe !important;
        color: #1e3a5f !important;
    }
    [data-testid="stAlertContainer"] [data-testid="stMarkdownContainer"] p {
        color: #1e3a5f !important;
        -webkit-text-fill-color: #1e3a5f !important;
    }
    .book-rating-summary {
        min-height: 5.2rem;
        margin-bottom: 0.4rem;
        padding: 0.5rem 0.65rem;
        background-color: #fffaf0;
        border: 1px solid #f0dfb0;
        border-radius: 0.6rem;
    }
    .book-title-card {
        min-height: 2.8rem;
        margin: 0.25rem 0 0.65rem;
        padding: 0.55rem 0.75rem;
        background-color: #edf7f1;
        border: 1px solid #c9e3d4;
        border-left: 4px solid #167653;
        border-radius: 0.45rem;
        color: #173c2f;
        font-size: 1.08rem;
        font-weight: 700;
        line-height: 1.45;
        overflow-wrap: anywhere;
    }
    .book-title-card.is-empty {
        background-color: #f7f9f8;
        border-color: #e0e7e3;
        border-left-color: #aebfb7;
        color: #667987;
        font-size: 0.95rem;
        font-weight: 500;
    }
    .book-rating-label {
        color: #263746;
        font-size: 0.86rem;
        line-height: 1.25;
    }
    .book-rating-score {
        margin-top: 0.12rem;
        color: #946200;
        font-size: 1.12rem;
        font-weight: 700;
        line-height: 1.35;
    }
    .book-rating-star {
        color: #e0a800;
    }
    .book-rating-out-of {
        color: #946200;
        font-size: 0.88rem;
        font-weight: 600;
    }
    .book-rating-count {
        margin-top: 0.05rem;
        color: #52616b;
        font-size: 0.75rem;
        line-height: 1.25;
    }
    [class*="st-key-book-rating-"] [data-testid="stFormSubmitButton"] button {
        min-height: 2rem;
        padding: 0.2rem 0.5rem;
        font-size: 0.85rem;
    }
    [data-testid="stTabs"] button[role="tab"] {
        color: #355b50;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background-color: #e3f2eb !important;
        border-bottom: 3px solid #167653 !important;
        color: #145c42 !important;
        font-weight: 700;
    }
    [data-testid="stTabs"] button[role="tab"]:focus-visible,
    [data-testid="stButton"] button:focus-visible,
    [data-testid="stFormSubmitButton"] button:focus-visible,
    [data-testid="stBaseButton-primaryFormSubmit"]:focus-visible,
    [data-testid="stBaseButton-secondaryFormSubmit"]:focus-visible {
        outline: 3px solid #f0ad3d !important;
        outline-offset: 2px;
        z-index: 1;
    }
    [data-testid="stButton"] button {
        background-color: #ffffff !important;
        border: 1px solid #a9cdbd !important;
        color: #145c42 !important;
    }
    [data-testid="stButton"] button * {
        color: #145c42 !important;
        -webkit-text-fill-color: #145c42 !important;
    }
    [data-testid="stButton"] button:hover,
    [data-testid="stButton"] button:active {
        background-color: #e3f2eb !important;
        border-color: #167653 !important;
        color: #104b36 !important;
    }
    [data-testid="stButton"] button:hover *,
    [data-testid="stButton"] button:active * {
        color: #104b36 !important;
        -webkit-text-fill-color: #104b36 !important;
    }
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stBaseButton-primaryFormSubmit"],
    [data-testid="stBaseButton-secondaryFormSubmit"] {
        background-color: #167653 !important;
        border: 1px solid #126447 !important;
        color: #ffffff !important;
        min-height: 2.8rem;
        font-weight: 700;
    }
    [data-testid="stFormSubmitButton"] button *,
    [data-testid="stBaseButton-primaryFormSubmit"] *,
    [data-testid="stBaseButton-secondaryFormSubmit"] * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    [data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stBaseButton-primaryFormSubmit"]:hover,
    [data-testid="stBaseButton-secondaryFormSubmit"]:hover {
        background-color: #105f42 !important;
        border-color: #0d5138 !important;
    }
    [data-testid="stFormSubmitButton"] button:focus-visible,
    [data-testid="stBaseButton-primaryFormSubmit"]:focus-visible,
    [data-testid="stBaseButton-secondaryFormSubmit"]:focus-visible {
        background-color: #105f42 !important;
        border-color: #0d5138 !important;
        color: #ffffff !important;
    }
    [data-testid="stFormSubmitButton"] button:active,
    [data-testid="stBaseButton-primaryFormSubmit"]:active,
    [data-testid="stBaseButton-secondaryFormSubmit"]:active {
        background-color: #105f42 !important;
        border-color: #0d5138 !important;
        color: #ffffff !important;
    }
    [data-testid="stFormSubmitButton"] button:active *,
    [data-testid="stBaseButton-primaryFormSubmit"]:active *,
    [data-testid="stBaseButton-secondaryFormSubmit"]:active *,
    [data-testid="stFormSubmitButton"] button:focus-visible *,
    [data-testid="stBaseButton-primaryFormSubmit"]:focus-visible *,
    [data-testid="stBaseButton-secondaryFormSubmit"]:focus-visible * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] input,
    [data-testid="stMultiSelect"] input {
        background-color: #ffffff !important;
        color: #263746 !important;
        -webkit-text-fill-color: #263746 !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"]:focus-within > div {
        background-color: #ffffff !important;
        border-color: #167653 !important;
        color: #263746 !important;
        -webkit-text-fill-color: #263746 !important;
        box-shadow: 0 0 0 2px rgba(22, 118, 83, 0.2) !important;
    }
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #263746 !important;
    }
    [data-testid="stSelectbox"] [role="group"],
    [data-testid="stMultiSelect"] [role="group"] {
        background-color: #ffffff !important;
        border: 1px solid #aebfb7 !important;
        border-radius: 0.5rem;
        color: #263746 !important;
    }
    [data-testid="stSelectbox"] [role="group"]:focus-within,
    [data-testid="stMultiSelect"] [role="group"]:focus-within {
        background-color: #ffffff !important;
        border-color: #167653 !important;
        box-shadow: 0 0 0 2px rgba(22, 118, 83, 0.2) !important;
    }
    [data-testid="stSelectbox"] [role="group"] input,
    [data-testid="stMultiSelect"] [role="group"] input {
        background-color: transparent !important;
        color: #263746 !important;
        -webkit-text-fill-color: #263746 !important;
    }
    [data-testid="stSelectbox"] [role="group"] button,
    [data-testid="stMultiSelect"] [role="group"] button {
        background-color: transparent !important;
        color: #263746 !important;
    }
    [data-testid="stSelectbox"] [data-baseweb="select"] div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] div {
        color: #263746 !important;
        -webkit-text-fill-color: #263746 !important;
    }
    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder,
    [data-testid="stSelectbox"] input::placeholder,
    [data-testid="stMultiSelect"] input::placeholder {
        color: #667987 !important;
        -webkit-text-fill-color: #667987 !important;
        opacity: 1;
    }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background-color: #dcefe8;
        color: #263746;
    }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] span {
        color: #263746 !important;
    }
    [data-baseweb="popover"] [role="option"],
    [role="listbox"] [role="option"] {
        background-color: #ffffff !important;
        color: #263746 !important;
    }
    [data-baseweb="popover"] [role="option"][aria-selected="true"],
    [data-baseweb="popover"] [role="option"]:hover,
    [data-baseweb="popover"] [role="option"]:focus,
    [role="listbox"] [role="option"][aria-selected="true"],
    [role="listbox"] [role="option"]:hover,
    [role="listbox"] [role="option"]:focus {
        background-color: #dcefe8 !important;
        color: #173c2f !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "rating_voter_id" not in st.session_state:
    st.session_state["rating_voter_id"] = str(uuid.uuid4())
voter_id = st.session_state["rating_voter_id"]

try:
    textbooks = load_textbooks()
except (json.JSONDecodeError, OSError, ValueError) as error:
    textbooks = []
    st.error(f"教科書データを読み込めませんでした：{error}")

tab_list, tab_add = st.tabs(["教科書一覧", "教科書を追加"])

with tab_add:
    st.subheader("新しい情報を追加")
    st.caption("同じ授業名・教授名の登録がある場合は、既存情報に統合されます。")
    with st.form("textbook_form", clear_on_submit=True):
        department = st.multiselect("学科（必須・複数選択可）", DEPARTMENTS)
        grade = st.multiselect("学年（必須・複数選択可）", GRADES)
        lecture_name = st.text_input(
            "授業名（必須）",
            placeholder="授業名を入力",
        )
        professor_name = st.text_input(
            "教授名（必須）",
            placeholder="教授名を入力",
        )

        col1, col2 = st.columns(2)
        with col1:
            required_textbook = st.text_input(
                "指定教科書名",
                placeholder="指定教科書名を入力",
            )
        with col2:
            reference_book = st.text_input(
                "市販参考書",
                placeholder="市販参考書を入力",
            )

        st.markdown("**教科書ごとのわかりやすさ（任意）**")
        clarity_col1, clarity_col2 = st.columns(2)
        with clarity_col1:
            initial_clarity = st.selectbox(
                (
                    f"『{required_textbook}』のわかりやすさ"
                    if required_textbook
                    else "指定教科書のわかりやすさ"
                ),
                RATING_CHOICES,
                disabled=not required_textbook,
            )
        with clarity_col2:
            initial_reference_clarity = st.selectbox(
                (
                    f"『{reference_book}』のわかりやすさ"
                    if reference_book
                    else "市販参考書のわかりやすさ"
                ),
                RATING_CHOICES,
                disabled=not reference_book,
            )
        st.markdown("**教科書ごとの授業での使用頻度（任意）**")
        frequency_col1, frequency_col2 = st.columns(2)
        with frequency_col1:
            initial_frequency = st.selectbox(
                (
                    f"『{required_textbook}』の使用頻度"
                    if required_textbook
                    else "指定教科書の使用頻度"
                ),
                RATING_CHOICES,
                disabled=not required_textbook,
            )
        with frequency_col2:
            initial_reference_frequency = st.selectbox(
                (
                    f"『{reference_book}』の使用頻度"
                    if reference_book
                    else "市販参考書の使用頻度"
                ),
                RATING_CHOICES,
                disabled=not reference_book,
            )

        submitted = st.form_submit_button("追加する", use_container_width=True)

        if submitted:
            try:
                add_textbook(
                    lecture_name or "",
                    professor_name or "",
                    required_textbook or "",
                    reference_book or "",
                    department=department,
                    grade=grade,
                    clarity_rating=_rating_value(initial_clarity),
                    frequency_rating=_rating_value(initial_frequency),
                    voter_id=voter_id,
                    reference_clarity_rating=_rating_value(
                        initial_reference_clarity
                    ),
                    reference_frequency_rating=_rating_value(
                        initial_reference_frequency
                    ),
                )
                st.success("教科書情報を追加しました")
                st.rerun()
            except (ValueError, OSError) as error:
                st.error(str(error))

with tab_list:
    selected_departments = st.multiselect(
        "学科で絞り込む（複数選択可）",
        DEPARTMENTS,
    )
    selected_grades = st.multiselect(
        "学年で絞り込む（複数選択可）",
        GRADES,
    )

    search = st.text_input(
        "学科・学年・授業名・教授名・教科書名で検索",
        placeholder="キーワードを入力",
    )

    if textbooks:
        filtered = []
        for item in textbooks:
            department_matches = bool(
                selected_departments
                and set(selected_departments).intersection(item["department"])
            )
            grade_matches = bool(
                selected_grades and set(selected_grades).intersection(item["grade"])
            )
            if (
                (not selected_departments and not selected_grades)
                or department_matches
                or grade_matches
            ):
                filtered.append(item)
        keyword = search.strip().lower()
        if keyword:
            filtered = [
                item
                for item in filtered
                if any(
                    keyword in value.lower()
                    for value in (
                        *item["department"],
                        *item["grade"],
                        item["lecture_name"],
                        item["professor_name"],
                        item["required_textbook"],
                        item["reference_book"],
                    )
                )
            ]

        st.caption(f"{len(filtered)} 件")
        if filtered:
            for item in filtered:
                department_label = "・".join(item["department"]) or "学科未登録"
                grade_label = "・".join(item["grade"]) or "学年未登録"
                title = (
                    f"{department_label}・{grade_label} | {item['lecture_name']} "
                    f"- {item['professor_name']}教授"
                )
                with st.expander(title, expanded=False):
                    st.markdown(f"**学科：** {department_label}")
                    st.markdown(f"**学年：** {grade_label}")

                    if item["creator_id"] == voter_id:
                        with st.form(key=f"edit-form-{item['id']}"):
                            st.markdown("**登録情報を編集**")
                            edited_departments = st.multiselect(
                                "学科",
                                DEPARTMENTS,
                                default=[
                                    department
                                    for department in item["department"]
                                    if department in DEPARTMENTS
                                ],
                                key=f"edit-department-{item['id']}",
                            )
                            edited_grades = st.multiselect(
                                "学年",
                                GRADES,
                                default=[
                                    grade for grade in item["grade"] if grade in GRADES
                                ],
                                key=f"edit-grade-{item['id']}",
                            )
                            edited_lecture_name = st.text_input(
                                "授業名",
                                value=item["lecture_name"],
                                key=f"edit-lecture-{item['id']}",
                            )
                            edited_professor_name = st.text_input(
                                "教授名",
                                value=item["professor_name"],
                                key=f"edit-professor-{item['id']}",
                            )
                            edited_required_textbook = st.text_input(
                                "指定教科書名",
                                value=item["required_textbook"],
                                key=f"edit-required-book-{item['id']}",
                            )
                            edited_reference_book = st.text_input(
                                "市販参考書",
                                value=item["reference_book"],
                                key=f"edit-reference-book-{item['id']}",
                            )
                            if st.form_submit_button(
                                "登録情報を更新",
                                use_container_width=True,
                            ):
                                try:
                                    update_textbook(
                                        item["id"],
                                        voter_id,
                                        edited_lecture_name,
                                        edited_professor_name,
                                        edited_required_textbook,
                                        edited_reference_book,
                                        department=edited_departments,
                                        grade=edited_grades,
                                    )
                                    st.success("登録情報を更新しました")
                                    st.rerun()
                                except (ValueError, OSError) as error:
                                    st.error(str(error))

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**指定教科書**")
                        if item["required_textbook"]:
                            required_book = html.escape(item["required_textbook"])
                            st.markdown(
                                f'<div class="book-title-card">{required_book}</div>',
                                unsafe_allow_html=True,
                            )
                            clarity_col, frequency_col = st.columns(2, gap="small")
                            with clarity_col:
                                _render_book_rating(
                                    item,
                                    "required_textbook",
                                    "book_clarity",
                                    "わかりやすさ",
                                    voter_id,
                                )
                            with frequency_col:
                                _render_book_rating(
                                    item,
                                    "required_textbook",
                                    "book_frequency",
                                    "授業での使用頻度",
                                    voter_id,
                                )
                            _render_book_reviews(
                                item,
                                "required_textbook",
                                item["required_textbook"],
                            )
                        else:
                            st.caption("指定教科書は未登録です")

                    with col2:
                        st.markdown("**市販参考書**")
                        if item["reference_book"]:
                            reference_book = html.escape(item["reference_book"])
                            st.markdown(
                                f'<div class="book-title-card">{reference_book}</div>',
                                unsafe_allow_html=True,
                            )
                        if item["reference_book"]:
                            clarity_col, frequency_col = st.columns(2, gap="small")
                            with clarity_col:
                                _render_book_rating(
                                    item,
                                    "reference_book",
                                    "book_clarity",
                                    "わかりやすさ",
                                    voter_id,
                                )
                            with frequency_col:
                                _render_book_rating(
                                    item,
                                    "reference_book",
                                    "book_frequency",
                                    "授業での使用頻度",
                                    voter_id,
                                )
                            _render_book_reviews(
                                item,
                                "reference_book",
                                item["reference_book"],
                            )
                        else:
                            st.caption("市販参考書は未登録です")

        else:
            st.info("該当する教科書情報はありません")
    else:
        st.info("まだ教科書情報が登録されていません")