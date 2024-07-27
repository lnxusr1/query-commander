#!/usr/bin/env python

import sys
import re

import os
import datetime
import hashlib
import secrets
from base64 import urlsafe_b64encode, urlsafe_b64decode
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def generate_session_token():
    random_bytes = secrets.token_bytes(32)
    session_token = hashlib.sha256(random_bytes).hexdigest()

    return session_token

def get_utc_now():
    try:
        return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    except:
        return datetime.datetime.utcnow()

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


if __name__ == "__main__":
    print("Location: /\n")
    sys.exit()