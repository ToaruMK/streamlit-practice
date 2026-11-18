import json
import os
import tempfile
import uuid
from pathlib import Path
from threading import Lock


DATA_FILE = Path(__file__).parent.parent / "sample_data" / "textbooks.json"
_write_lock = Lock()


def _normalize_choices(value):
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = []
    return list(dict.fromkeys(str(item).strip() for item in values if str(item).strip()))


def _normalize_ratings(value):
    normalized = {"clarity": [], "frequency": []}
    if not isinstance(value, dict):
        return normalized

    for metric in normalized:
        votes = value.get(metric, [])
        if not isinstance(votes, list):
            continue
        voters = set()
        for vote in votes:
            if not isinstance(vote, dict):
                continue
            voter_id = str(vote.get("voter_id", "")).strip()
            try:
                rating = int(vote.get("value"))
            except (TypeError, ValueError):
                continue
            if not voter_id or voter_id in voters or not 1 <= rating <= 5:
                continue
            voters.add(voter_id)
            normalized[metric].append({"voter_id": voter_id, "value": rating})
    return normalized


def _normalize_record(record):
    if hasattr(record, "__dict__"):
        record = record.__dict__
    if not isinstance(record, dict):
        raise TypeError("教科書情報は辞書またはオブジェクトで指定してください")

    ratings = _normalize_ratings(record.get("ratings", {}))
    creator_id = str(record.get("creator_id", "")).strip()
    if not creator_id:
        voter_ids = {
            vote["voter_id"]
            for votes in ratings.values()
            for vote in votes
        }
        if len(voter_ids) == 1:
            creator_id = voter_ids.pop()
    creator_ids = _normalize_choices(record.get("creator_ids", []))
    if creator_id and creator_id not in creator_ids:
        creator_ids.append(creator_id)

    normalized = {
        "id": str(record.get("id", "")).strip(),
        "creator_id": creator_id,
        "creator_ids": creator_ids,
        "department": _normalize_choices(
            record.get("department", record.get("学科", ""))
        ),
        "grade": _normalize_choices(record.get("grade", record.get("学年", ""))),
        "lecture_name": str(record.get("lecture_name", record.get("講義名", ""))).strip(),
        "professor_name": str(record.get("professor_name", record.get("教授名", ""))).strip(),
        "required_textbook": str(
            record.get("required_textbook", record.get("指定教科書", ""))
        ).strip(),
        "reference_book": str(
            record.get("reference_book", record.get("市販参考書", ""))
        ).strip(),
        "ratings": ratings,
        "comments": [],
    }
    if not normalized["id"]:
        normalized["id"] = str(uuid.uuid4())

    comments = record.get("comments", [])
    if isinstance(comments, list):
        for comment in comments:
            if hasattr(comment, "__dict__"):
                comment = comment.__dict__
            if not isinstance(comment, dict):
                continue
            text = str(comment.get("text", "")).strip()
            if not text:
                continue
            try:
                likes = int(comment.get("likes", 0))
            except (TypeError, ValueError):
                likes = 0
            normalized["comments"].append(
                {
                    "id": str(comment.get("id", "")).strip() or str(uuid.uuid4()),
                    "text": text,
                    "likes": max(0, likes),
                }
            )
    return normalized


def load_textbooks(path=None):
    """JSONファイルから教科書情報を読み込む。ファイルがない場合は空リストを返す。"""
    data_path = Path(path) if path is not None else DATA_FILE
    if not data_path.exists():
        return []

    with data_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("教科書データはJSON配列で保存してください")
    return [_normalize_record(record) for record in data]


def save_textbooks(records, path=None):
    """教科書情報をアトミックにJSONへ保存する。"""
    data_path = Path(path) if path is not None else DATA_FILE
    data_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [_normalize_record(record) for record in records]

    with _write_lock:
        fd, temp_name = tempfile.mkstemp(
            dir=str(data_path.parent), prefix=".textbooks-", suffix=".json"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(normalized, file, ensure_ascii=False, indent=2)
                file.write("\n")
            os.replace(temp_name, data_path)
        except Exception:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
            raise

    return normalized


def add_textbook(
    lecture_name,
    professor_name,
    required_textbook,
    reference_book="",
    path=None,
    department="",
    grade="",
    clarity_rating=None,
    frequency_rating=None,
    voter_id=None,
):
    """教科書情報を検証して追加する。"""
    record = _normalize_record(
        {
            "id": str(uuid.uuid4()),
            "creator_id": str(voter_id or "").strip(),
            "department": department,
            "grade": grade,
            "lecture_name": lecture_name,
            "professor_name": professor_name,
            "required_textbook": required_textbook,
            "reference_book": reference_book,
            "ratings": {"clarity": [], "frequency": []},
            "comments": [],
        }
    )

    required_fields = (
        ("department", "学科"),
        ("grade", "学年"),
        ("lecture_name", "授業名"),
        ("professor_name", "教授名"),
        ("required_textbook", "指定教科書"),
    )
    missing = [label for key, label in required_fields if not record[key]]
    if missing:
        raise ValueError(f"{'・'.join(missing)}は必須です")

    initial_ratings = {
        "clarity": clarity_rating,
        "frequency": frequency_rating,
    }
    if voter_id:
        for metric, rating in initial_ratings.items():
            if rating is not None:
                _validate_rating(rating)
                record["ratings"][metric].append(
                    {"voter_id": str(voter_id), "value": int(rating)}
                )

    records = load_textbooks(path)
    matching_record = next(
        (
            existing
            for existing in records
            if existing["lecture_name"].casefold() == record["lecture_name"].casefold()
            and existing["professor_name"].casefold()
            == record["professor_name"].casefold()
        ),
        None,
    )
    if matching_record is not None:
        _merge_choices(matching_record["department"], record["department"])
        _merge_choices(matching_record["grade"], record["grade"])
        matching_record["required_textbook"] = _merge_text(
            matching_record["required_textbook"], record["required_textbook"]
        )
        matching_record["reference_book"] = _merge_text(
            matching_record["reference_book"], record["reference_book"]
        )
        matching_record["creator_ids"] = _merge_choices(
            matching_record["creator_ids"], record["creator_ids"]
        )
        for metric in ("clarity", "frequency"):
            matching_record["ratings"][metric].extend(record["ratings"][metric])
        matching_record["comments"].extend(record["comments"])
        save_textbooks(records, path)
        return matching_record

    records.append(record)
    save_textbooks(records, path)
    return record


def _merge_choices(existing, incoming):
    for value in incoming:
        if value not in existing:
            existing.append(value)
    return existing


def _merge_text(existing, incoming):
    values = [value.strip() for value in existing.splitlines() if value.strip()]
    for value in incoming.splitlines():
        value = value.strip()
        if value and value not in values:
            values.append(value)
    return "\n".join(values)


def update_textbook(
    textbook_id,
    creator_id,
    lecture_name,
    professor_name,
    required_textbook,
    reference_book="",
    department=None,
    grade=None,
    path=None,
):
    """登録者本人の教科書情報を更新する。"""
    editor_id = str(creator_id).strip()
    if not editor_id:
        raise ValueError("登録者を確認できません")

    records = load_textbooks(path)
    for record in records:
        if record["id"] != textbook_id:
            continue
        if editor_id not in record["creator_ids"]:
            raise PermissionError("この教科書情報を編集できるのは登録者本人だけです")

        updated_fields = {
            "department": _normalize_choices(
                record["department"] if department is None else department
            ),
            "grade": _normalize_choices(record["grade"] if grade is None else grade),
            "lecture_name": str(lecture_name).strip(),
            "professor_name": str(professor_name).strip(),
            "required_textbook": str(required_textbook).strip(),
            "reference_book": str(reference_book).strip(),
        }
        required_fields = (
            ("department", "学科"),
            ("grade", "学年"),
            ("lecture_name", "授業名"),
            ("professor_name", "教授名"),
            ("required_textbook", "指定教科書"),
        )
        missing = [label for key, label in required_fields if not updated_fields[key]]
        if missing:
            raise ValueError(f"{'・'.join(missing)}は必須です")

        record.update(updated_fields)
        save_textbooks(records, path)
        return record
    raise ValueError("教科書が見つかりません")


def _validate_rating(value):
    try:
        rating = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("評価は1〜5の星で指定してください") from error
    if rating != value or not 1 <= rating <= 5:
        raise ValueError("評価は1〜5の星で指定してください")
    return rating


def rate_textbook(textbook_id, metric, value, voter_id, path=None):
    """利用者の教科書評価を追加または更新する。"""
    if metric not in ("clarity", "frequency"):
        raise ValueError("評価項目が正しくありません")
    rating = _validate_rating(value)
    voter = str(voter_id).strip()
    if not voter:
        raise ValueError("評価者を識別できません")

    records = load_textbooks(path)
    for record in records:
        if record["id"] == textbook_id:
            votes = record["ratings"][metric]
            for vote in votes:
                if vote["voter_id"] == voter:
                    vote["value"] = rating
                    break
            else:
                votes.append({"voter_id": voter, "value": rating})
            save_textbooks(records, path)
            return rating_summary(record, metric)
    raise ValueError("教科書が見つかりません")


def rating_summary(record, metric):
    """評価平均と評価人数を返す。"""
    votes = record.get("ratings", {}).get(metric, [])
    if not votes:
        return {"average": None, "count": 0}
    return {
        "average": sum(vote["value"] for vote in votes) / len(votes),
        "count": len(votes),
    }


def add_comment(textbook_id, text, path=None):
    """指定した教科書にコメントを追加する。"""
    comment_text = str(text).strip()
    if not comment_text:
        raise ValueError("コメントを入力してください")

    records = load_textbooks(path)
    for record in records:
        if record["id"] == textbook_id:
            record["comments"].append(
                {
                    "id": str(uuid.uuid4()),
                    "text": comment_text,
                    "likes": 0,
                }
            )
            save_textbooks(records, path)
            return record["comments"][-1]
    raise ValueError("教科書が見つかりません")


def like_comment(textbook_id, comment_id, path=None):
    """指定したコメントのグッド数を1増やす。"""
    records = load_textbooks(path)
    for record in records:
        if record["id"] == textbook_id:
            for comment in record["comments"]:
                if comment["id"] == comment_id:
                    comment["likes"] += 1
                    save_textbooks(records, path)
                    return comment
            raise ValueError("コメントが見つかりません")
    raise ValueError("教科書が見つかりません")