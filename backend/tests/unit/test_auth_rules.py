import pytest
from pydantic import ValidationError

from app.core.security import csrf_matches, hash_password, new_token, token_digest, verify_password
from app.modules.auth.schemas import Credentials


@pytest.mark.parametrize("name", ["abc", "Ab_123", "旅行同学", "a" * 20, "  Travel_01  "])
def test_username_acceptance(name):
    assert Credentials(username=name, password="password").username == name.strip()


@pytest.mark.parametrize("name", ["ab", "a" * 21, "a b", "test@user", "１２３", "用户😀", "   ", None, 123, True])
def test_username_rejection(name):
    with pytest.raises(ValidationError):
        Credentials(username=name, password="password")


@pytest.mark.parametrize("password", ["a" * 8, "a" * 64, "  abcdef", "汉" * 8, "😀" * 8])
def test_password_original_value(password):
    assert Credentials(username="tester", password=password).password == password


@pytest.mark.parametrize("password", ["a" * 7, "a" * 65, "", None, 123, True])
def test_invalid_password(password):
    with pytest.raises(ValidationError):
        Credentials(username="tester", password=password)


def test_no_role_in_public_input():
    with pytest.raises(ValidationError):
        Credentials(username="tester", password="password", role="admin")


def test_argon2id_and_random_salts():
    first = hash_password("  abcdef")
    second = hash_password("  abcdef")
    assert first.startswith("$argon2id$")
    assert first != second
    assert verify_password("  abcdef", first)
    assert not verify_password("abcdef  ", first)
    assert not verify_password("password", None)
    assert not verify_password("password", "corrupted-hash")


def test_tokens_and_constant_time_comparison_support_unicode():
    first, second = new_token(), new_token()
    assert first != second
    assert len(token_digest(first)) == 32
    assert csrf_matches(first, first)
    assert not csrf_matches(None, first)
    assert not csrf_matches("伪造令牌", first)
