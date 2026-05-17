"""
Unit tests for auth utilities (password hashing + JWT).
No database or network calls needed.
"""
import time
from api.models.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


class TestPasswordHashing:

    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mysecretpass")
        assert "mysecretpass" not in hashed

    def test_verify_correct_password(self):
        hashed = hash_password("correctpassword")
        assert verify_password("correctpassword", hashed) is True

    def test_reject_wrong_password(self):
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_same_password_produces_different_hashes(self):
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2  # different salts

    def test_verify_invalid_hash_returns_false(self):
        assert verify_password("any", "not-a-valid-hash") is False

    def test_verify_empty_password(self):
        hashed = hash_password("realpassword")
        assert verify_password("", hashed) is False


class TestJWT:

    def test_create_and_decode_token(self):
        token = create_access_token(user_id=1, username="bhanu")
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["username"] == "bhanu"

    def test_token_has_three_parts(self):
        token = create_access_token(1, "bhanu")
        assert len(token.split(".")) == 3

    def test_tampered_token_rejected(self):
        token = create_access_token(1, "bhanu")
        parts = token.split(".")
        # Tamper with payload
        tampered = parts[0] + ".TAMPERED" + parts[2]
        assert decode_access_token(tampered) is None

    def test_wrong_signature_rejected(self):
        token = create_access_token(1, "bhanu")
        parts = token.split(".")
        bad_token = parts[0] + "." + parts[1] + ".badsignature"
        assert decode_access_token(bad_token) is None

    def test_malformed_token_rejected(self):
        assert decode_access_token("not.a.valid.jwt.token") is None
        assert decode_access_token("") is None
        assert decode_access_token("onlyone") is None

    def test_expired_token_rejected(self):
        import json, base64
        # Build a token that expired in the past
        token = create_access_token(1, "bhanu")
        parts = token.split(".")

        def _b64decode(data):
            padding = 4 - len(data) % 4
            return base64.urlsafe_b64decode(data + "=" * padding)

        payload = json.loads(_b64decode(parts[1]))
        payload["exp"] = int(time.time()) - 3600  # 1 hour ago

        def _b64encode(data):
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        new_body = _b64encode(json.dumps(payload).encode())
        # Re-sign with correct key to test expiry logic specifically
        import hmac, hashlib
        from api.models.auth import SECRET_KEY
        signing_input = f"{parts[0]}.{new_body}"
        sig = _b64encode(
            hmac.new(SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
        )
        expired_token = f"{signing_input}.{sig}"
        assert decode_access_token(expired_token) is None

    def test_different_users_get_different_tokens(self):
        t1 = create_access_token(1, "user1")
        t2 = create_access_token(2, "user2")
        assert t1 != t2

    def test_payload_contains_expected_fields(self):
        token = create_access_token(42, "testuser")
        payload = decode_access_token(token)
        assert "sub" in payload
        assert "username" in payload
        assert "exp" in payload
        assert "iat" in payload
