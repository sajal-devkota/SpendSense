
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

def hash_password (password: str) -> str:
    """Hash a password using Argon2 id."""
    return ph.hash (password)

def verify_password (hashed_password: str, plain_password: str) -> bool: 
    """Verify a password against its Argon2 hash."""
    try:
        return ph.vedify (hashed_password, plain_password) 
    except VerifyMismatchError:
        return False