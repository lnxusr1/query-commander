import os
import re
import datetime
import hashlib
import secrets
from base64 import urlsafe_b64encode, urlsafe_b64decode
import uuid
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def generate_session_token():
    #random_bytes = secrets.token_bytes(32) + get_utc_now().strftime("%Y%m%d%H%M%S").encode()
    #session_token = hashlib.sha256(random_bytes).hexdigest()
    session_token = uuid.uuid4().hex
    return session_token

def get_utc_now():
    try:
        return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    except:
        return datetime.datetime.utcnow()

def quote_ident(identifier):
    # Ensure the identifier is a valid schema name (e.g., no special characters)
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', identifier):
        raise ValueError("Invalid schema name")
    return f'"{identifier}"'

# Validate a string is reasonable.  This is not a perfect test.
def validate_string(text, is_username=False, max_length=None):
    if text == "" or text is None:
        return False
    
    # Check length
    if max_length is not None and len(text) > max_length:
        return False

    # Check if the text starts and ends with an alphanumeric character
    if is_username and (not text[0].isalnum() or not text[-1].isalnum()):
        return False

    # Check for valid characters (alphanumeric, dots, hyphens, underscores)
    if not re.match("^[a-zA-Z0-9][a-zA-Z0-9_.-]*[a-zA-Z0-9]$", text):
        return False

    # If all conditions pass, the text is considered valid
    return True

# Key derivation function for generating a key from a password
def derive_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode('utf-8'))
    return key

# Encrypt function
def encrypt(password, plaintext):
    salt = os.urandom(16)
    key = derive_key(password, salt)
    iv = os.urandom(16)  # Initialization Vector (IV) for CFB mode
    cipher = Cipher(algorithms.AES(key), modes.CFB8(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()
    return urlsafe_b64encode(salt + iv + ciphertext).decode('utf-8')

# Decrypt function
def decrypt(password, ciphertext):
    data = urlsafe_b64decode(ciphertext)
    salt, iv, ciphertext = data[:16], data[16:32], data[32:]
    key = derive_key(password, salt)
    cipher = Cipher(algorithms.AES(key), modes.CFB8(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext.decode('utf-8')

def get_page_content(page_name):
    if page_name == "index.html":
        with open(os.path.join(os.path.dirname(__file__), "..", "static", "index.html"), "r", encoding="UTF-8") as fp:
            text = fp.read()

        return text, { "Content-Type": "text/html" }

    if page_name == "script.js":
        with open(os.path.join(os.path.dirname(__file__), "..", "static", "script.js"), "r", encoding="UTF-8") as fp:
            text = fp.read()

        return text, { "Content-Type": "text/javascript" }

    if page_name == "favicon.svg":
        with open(os.path.join(os.path.dirname(__file__), "..", "static", "favicon.svg"), "r", encoding="UTF-8") as fp:
            text = fp.read()

        return text, { "Content-Type": "image/svg+xml" }

    if page_name == "logo.svg":
        with open(os.path.join(os.path.dirname(__file__), "..", "static", "logo.svg"), "r", encoding="UTF-8") as fp:
            text = fp.read()

        return text, { "Content-Type": "image/svg+xml" }

    if page_name == "structure.css":
        with open(os.path.join(os.path.dirname(__file__), "..", "static", "structure.css"), "r", encoding="UTF-8") as fp:
            text = fp.read()

        return text, { "Content-Type": "text/css" }

    if page_name == "theme.css":
        with open(os.path.join(os.path.dirname(__file__), "..", "static", "theme.css"), "r", encoding="UTF-8") as fp:
            text = fp.read()

        return text, { "Content-Type": "text/css" }

    if page_name == "bglogin.jpg":
        with open(os.path.join(os.path.dirname(__file__), "..", "static", "bglogin.jpg"), "rb") as fp:
            content = fp.read()

        return content, { "Content-Type": "image/jpeg" }

    if page_name == "logo.png":
        filename = os.path.join(os.path.dirname(__file__), "..", "static", "logo.png")
        file_size = os.path.getsize(filename)
        with open(filename, "rb") as fp:
            content = fp.read()

        import logging
        return content, { "Content-Type": "image/png", "Content-Length": str(file_size) }

    return "", { "Content-Type": "text/plain" }