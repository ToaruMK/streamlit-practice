import json
import importlib.util
import os
import uuid
from pathlib import Path

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

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
delete_textbook = textbook_model.delete_textbook

auth_module_path = PROJECT_ROOT / "models" / "admin_auth.py"
auth_spec = importlib.util.spec_from_file_location(
    "_streamlit_practice_admin_auth", auth_module_path
)
if auth_spec is None or auth_spec.loader is None:
    raise ImportError(f"管理者認証を読み込めませんでした：{auth_module_path}")
admin_auth = importlib.util.module_from_spec(auth_spec)
auth_spec.loader.exec_module(admin_auth)
verify_admin_password = admin_auth.verify_admin_password

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
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid #dcebe5;
        border-radius: 12px;
    }
    [data-testid="stTabs"] button[role="tab"] {
        color: #355b50;
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
        outline: 3px solid #f0ad3d !important;
        outline-offset: 2px;
    }
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] input,
    [data-testid="stMultiSelect"] input {
        background-color: #ffffff !important;
        color: #263746 !important;
        -webkit-text-fill-color: #263746 !important;
    }
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
        background-color: #ffffff !important;
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
    </style>
    """,
    unsafe_allow_html=True,
)

admin_password_hash = os.environ.get("TEXTBOOK_ADMIN_PASSWORD_HASH", "")
if not admin_password_hash:
    try:
        admin_password_hash = st.secrets.get("admin_password_hash", "")
    except StreamlitSecretNotFoundError:
        admin_password_hash = ""

with st.sidebar:
    st.subheader("管理者")
    if not admin_password_hash:
        st.warning(
            "管理者パスワードが未設定です。環境変数 "
            "TEXTBOOK_ADMIN_PASSWORD_HASH または Streamlit Secrets の "
            "admin_password_hash を設定してください。"
        )
    elif st.session_state.get("is_admin") is True:
        st.success("管理者としてログイン中")
        if st.button("管理者ログアウト", use_container_width=True):
            st.session_state["is_admin"] = False
            st.rerun()
    else:
        with st.form("admin-login-form"):
            admin_password = st.text_input(
                "管理者パスワード",
                type="password",
            )
            if st.form_submit_button("管理者ログイン", use_container_width=True):
                if verify_admin_password(admin_password, admin_password_hash):
                    st.session_state["is_admin"] = True
                    st.rerun()
                else:
                    st.error("パスワードが正しくありません")

if "rating_voter_id" not in st.session_state:
    st.session_state["rating_voter_id"] = str(uuid.uuid4())
voter_id = st.session_state["rating_voter_id"]

try:
    textbooks = load_textbooks()
except (json.JSONDecodeError, OSError, ValueError) as error:
    textbooks = []
    st.error(f"教科書データを読み込めませんでした：{error}")

professor_suggestions = sorted(
    {item["professor_name"] for item in textbooks if item["professor_name"]}
)
lecture_suggestions = sorted(
    {item["lecture_name"] for item in textbooks if item["lecture_name"]}
)
required_book_suggestions = sorted(
    {item["required_textbook"] for item in textbooks if item["required_textbook"]}
)
reference_book_suggestions = sorted(
    {item["reference_book"] for item in textbooks if item["reference_book"]}
)

tab_list, tab_add = st.tabs(["教科書一覧", "教科書を追加"])

with tab_add:
    st.subheader("新しい情報を追加")
    st.caption("同じ授業名・教授名の登録がある場合は、既存情報に統合されます。")
    with st.form("textbook_form", clear_on_submit=True):
        department = st.multiselect("学科（必須・複数選択可）", DEPARTMENTS)
        grade = st.multiselect("学年（必須・複数選択可）", GRADES)
        lecture_name = st.selectbox(
            "授業名（必須）",
            lecture_suggestions,
            index=None,
            accept_new_options=True,
            placeholder="入力するか、過去の登録候補から選択",
        )
        professor_name = st.selectbox(
            "教授名（必須）",
            professor_suggestions,
            index=None,
            accept_new_options=True,
            placeholder="入力するか、過去の登録候補から選択",
        )

        col1, col2 = st.columns(2)
        with col1:
            required_textbook = st.selectbox(
                "指定教科書名（必須）",
                required_book_suggestions,
                index=None,
                accept_new_options=True,
                placeholder="入力するか、過去の登録候補から選択",
            )
        with col2:
            reference_book = st.selectbox(
                "市販参考書",
                reference_book_suggestions,
                index=None,
                accept_new_options=True,
                placeholder="入力するか、過去の登録候補から選択",
            )

        st.markdown("**教科書ごとのわかりやすさ（任意）**")
        clarity_col1, clarity_col2 = st.columns(2)
        with clarity_col1:
            initial_clarity = st.selectbox(
                "指定教科書のわかりやすさ",
                RATING_CHOICES,
            )
        with clarity_col2:
            initial_reference_clarity = st.selectbox(
                "市販参考書のわかりやすさ",
                RATING_CHOICES,
            )
        initial_frequency = st.selectbox(
            "授業での使用頻度（任意）",
            RATING_CHOICES,
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
                        st.write(item["required_textbook"] or "未登録")
                        required_summary = rating_summary(
                            item,
                            "book_clarity",
                            "required_textbook",
                        )
                        required_average = (
                            f"★ {required_summary['average']:.1f} / 5"
                            if required_summary["average"] is not None
                            else "評価なし"
                        )
                        st.metric("この教科書のわかりやすさ", required_average)
                        st.caption(
                            f"評価した人数：{required_summary['count']}人"
                        )
                        required_vote = next(
                            (
                                vote["value"]
                                for vote in item["ratings"]["book_clarity"][
                                    "required_textbook"
                                ]
                                if vote["voter_id"] == voter_id
                            ),
                            None,
                        )
                        with st.form(key=f"required-clarity-{item['id']}"):
                            required_clarity_choice = st.selectbox(
                                "この指定教科書を評価",
                                RATING_CHOICES,
                                index=required_vote or 0,
                                key=f"required-clarity-choice-{item['id']}",
                            )
                            if st.form_submit_button(
                                "指定教科書の評価を保存",
                                use_container_width=True,
                            ):
                                value = _rating_value(required_clarity_choice)
                                if value is None:
                                    st.info("星を選んでから評価を保存してください")
                                else:
                                    try:
                                        rate_textbook(
                                            item["id"],
                                            "book_clarity",
                                            value,
                                            voter_id,
                                            book_type="required_textbook",
                                        )
                                        st.success("指定教科書の評価を保存しました")
                                        st.rerun()
                                    except (ValueError, OSError) as error:
                                        st.error(str(error))
                    with col2:
                        st.markdown("**市販参考書**")
                        st.write(item["reference_book"] or "未登録")
                        if item["reference_book"]:
                            reference_summary = rating_summary(
                                item,
                                "book_clarity",
                                "reference_book",
                            )
                            reference_average = (
                                f"★ {reference_summary['average']:.1f} / 5"
                                if reference_summary["average"] is not None
                                else "評価なし"
                            )
                            st.metric("この参考書のわかりやすさ", reference_average)
                            st.caption(
                                f"評価した人数：{reference_summary['count']}人"
                            )
                            reference_vote = next(
                                (
                                    vote["value"]
                                    for vote in item["ratings"]["book_clarity"][
                                        "reference_book"
                                    ]
                                    if vote["voter_id"] == voter_id
                                ),
                                None,
                            )
                            with st.form(key=f"reference-clarity-{item['id']}"):
                                reference_clarity_choice = st.selectbox(
                                    "この市販参考書を評価",
                                    RATING_CHOICES,
                                    index=reference_vote or 0,
                                    key=f"reference-clarity-choice-{item['id']}",
                                )
                                if st.form_submit_button(
                                    "市販参考書の評価を保存",
                                    use_container_width=True,
                                ):
                                    value = _rating_value(reference_clarity_choice)
                                    if value is None:
                                        st.info(
                                            "星を選んでから評価を保存してください"
                                        )
                                    else:
                                        try:
                                            rate_textbook(
                                                item["id"],
                                                "book_clarity",
                                                value,
                                                voter_id,
                                                book_type="reference_book",
                                            )
                                            st.success(
                                                "市販参考書の評価を保存しました"
                                            )
                                            st.rerun()
                                        except (ValueError, OSError) as error:
                                            st.error(str(error))
                        else:
                            st.caption("市販参考書は未登録です")

                    frequency_summary = rating_summary(item, "frequency")
                    frequency_average = (
                        f"★ {frequency_summary['average']:.1f} / 5"
                        if frequency_summary["average"] is not None
                        else "評価なし"
                    )
                    st.metric("授業での使用頻度", frequency_average)
                    st.caption(
                        f"評価した人数：{frequency_summary['count']}人"
                    )
                    current_frequency = next(
                        (
                            vote["value"]
                            for vote in item["ratings"]["frequency"]
                            if vote["voter_id"] == voter_id
                        ),
                        None,
                    )
                    with st.form(key=f"frequency-rating-{item['id']}"):
                        frequency_choice = st.selectbox(
                            "授業で使う頻度を評価",
                            RATING_CHOICES,
                            index=current_frequency or 0,
                            key=f"frequency-choice-{item['id']}",
                        )
                        if st.form_submit_button(
                            "使用頻度の評価を保存",
                            use_container_width=True,
                        ):
                            value = _rating_value(frequency_choice)
                            if value is None:
                                st.info("星を選んでから評価を保存してください")
                            else:
                                try:
                                    rate_textbook(
                                        item["id"],
                                        "frequency",
                                        value,
                                        voter_id,
                                    )
                                    st.success("使用頻度の評価を保存しました")
                                    st.rerun()
                                except (ValueError, OSError) as error:
                                    st.error(str(error))

                    st.divider()
                    comments = sorted(
                        item["comments"],
                        key=lambda comment: (-comment["likes"], comment["id"]),
                    )

                    with st.expander(
                        f"レビューを見る・投稿する（{len(comments)}件）",
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
                                        help=(
                                            "グッド済み"
                                            if voted
                                            else "このレビューにグッド"
                                        ),
                                    ):
                                        try:
                                            like_comment(item["id"], comment["id"])
                                            st.session_state[vote_key] = True
                                            st.rerun()
                                        except (ValueError, OSError) as error:
                                            st.error(str(error))
                        else:
                            st.caption("まだレビューはありません")

                        st.info(
                            "使う頻度（毎回・試験前など）、新品がよいか中古でもよいか、"
                            "教科書のわかりやすさを書くと、ほかの学生の参考になります。"
                        )
                        with st.form(
                            key=f"comment-form-{item['id']}",
                            clear_on_submit=True,
                        ):
                            comment_text = st.text_area(
                                "レビューを書く",
                                placeholder=(
                                    "例：毎回の授業で使います。書き込みがなければ中古で十分です。"
                                    "説明がわかりやすく、予習にも役立ちました。"
                                ),
                                key=f"comment-text-{item['id']}",
                            )
                            if st.form_submit_button(
                                "レビューを投稿",
                                use_container_width=True,
                            ):
                                try:
                                    add_comment(item["id"], comment_text)
                                    st.success("レビューを投稿しました")
                                    st.rerun()
                                except (ValueError, OSError) as error:
                                    st.error(str(error))

                    if st.session_state.get("is_admin") is True:
                        with st.expander("管理者操作"):
                            st.warning(
                                "教科書情報を削除すると、関連するレビューと評価も削除されます。"
                            )
                            confirm_delete = st.checkbox(
                                "この教科書情報一式を削除することを確認",
                                key=f"confirm-delete-{item['id']}",
                            )
                            if st.button(
                                "教科書情報を削除",
                                key=f"delete-textbook-{item['id']}",
                                disabled=not confirm_delete,
                                use_container_width=True,
                            ):
                                try:
                                    delete_textbook(
                                        item["id"],
                                        is_admin=(
                                            st.session_state.get("is_admin") is True
                                        ),
                                    )
                                    st.session_state.pop(
                                        f"confirm-delete-{item['id']}", None
                                    )
                                    st.success("教科書情報を削除しました")
                                    st.rerun()
                                except (PermissionError, ValueError, OSError) as error:
                                    st.error(str(error))
        else:
            st.info("該当する教科書情報はありません")
    else:
        st.info("まだ教科書情報が登録されていません")