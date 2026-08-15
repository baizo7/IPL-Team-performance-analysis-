"""
Unit tests for password hashing and verification security.
"""

from ipl_analytics.components.login_form import hash_password, verify_password


def test_password_hashing_and_verification():
    raw_pwd = "my_secret_password_123"
    hashed = hash_password(raw_pwd)
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("wrong_password", hashed) is False
