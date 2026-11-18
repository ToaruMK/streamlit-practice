import hashlib
import hmac


def verify_admin_password(password, encoded_hash):
    """PBKDF2-SHA256形式の保存済み管理者パスワードハッシュを検証する。"""
    try:
        algorithm, rounds_text, salt_hex, expected_hex = encoded_hash.split("$", 3)
        rounds = int(rounds_text)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
    except (AttributeError, TypeError, ValueError):
        return False

    if algorithm != "pbkdf2_sha256" or rounds < 100_000 or len(salt) < 16:
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        str(password).encode("utf-8"),
        salt,
        rounds,
    )
    return hmac.compare_digest(actual, expected)
