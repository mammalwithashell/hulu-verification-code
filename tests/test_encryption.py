import os
os.environ.setdefault("SECRET_ENCRYPTION_KEY", "test-key-for-unit-tests-only!!")

from app.encryption import encrypt_secret, decrypt_secret


def test_round_trip():
    plaintext = "my-app-password-123"
    ciphertext = encrypt_secret(plaintext)
    assert ciphertext != plaintext
    assert decrypt_secret(ciphertext) == plaintext


def test_different_plaintexts_produce_different_ciphertexts():
    a = encrypt_secret("password-a")
    b = encrypt_secret("password-b")
    assert a != b


def test_ciphertext_is_string():
    ct = encrypt_secret("hello")
    assert isinstance(ct, str)


def test_empty_string_round_trip():
    ct = encrypt_secret("")
    assert decrypt_secret(ct) == ""
