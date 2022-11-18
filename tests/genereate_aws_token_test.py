"""Generate AWS token test file."""
from __future__ import annotations

from base64 import b64decode, b64encode
import hashlib
import os
import secrets

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from custom_components.mydolphin_plus.component.helpers.const import (
    API_REQUEST_SERIAL_EMAIL,
    API_REQUEST_SERIAL_NUMBER,
)

BLOCK_SIZE = 16


class AWSTokenGenerator:
    """test class."""

    def __init__(self, key: str):
        """Do initialization of the test file, Returns none."""
        print(f"Initializing, Key: {key}")

        self._backend = default_backend()

        self._iv = secrets.token_bytes(BLOCK_SIZE)

        self._mode = modes.CBC(self._iv)
        print(
            f"Mode: {self._mode.name}, initialization_vector: {self._mode.initialization_vector}"
        )

        self._aes_key = self._get_key(email)
        print("")

    @staticmethod
    def _get_key(key: str):
        key_beginning = key[:2]

        password = f"{key_beginning}ha".lower()
        print(f"password: {password}")

        password_bytes = password.encode()
        print(f"password_bytes: {password_bytes}")

        encryption_hash = hashlib.md5(password_bytes, usedforsecurity=False)
        encryption_key = encryption_hash.digest()
        print(f"encryption_key: {encryption_key}")

        return encryption_key

    def _get_cipher(self):
        cipher = Cipher(
            algorithms.AES(self._aes_key), self._mode, backend=self._backend
        )

        return cipher

    @staticmethod
    def _pad(text) -> str:
        text_length = len(text)
        amount_to_pad = BLOCK_SIZE - (text_length % BLOCK_SIZE)

        if amount_to_pad == 0:
            amount_to_pad = BLOCK_SIZE

        pad = chr(amount_to_pad)

        result = text + pad * amount_to_pad

        return result

    @staticmethod
    def _un_pad(text):
        pos = -1 * (text[-1])
        result = text[:pos]

        return result

    def encrypt(self, sn: str) -> str | None:
        """Do encryption of input string, Returns encrypted base 64 string."""

        print(f"ENCRYPT: Serial number: {sn}")

        data = self._pad(sn).encode()
        print(f"pad_data: {data}, Length: {len(data)}")

        cipher = self._get_cipher()
        encryptor = cipher.encryptor()
        ct = encryptor.update(data) + encryptor.finalize()
        print(f"ct: {ct}")

        encrypted_data = ct
        print(f"encrypted_data: {encrypted_data}, Length: {len(encrypted_data)}")

        result_b64 = self._iv + ct
        print(f"result_b64: {result_b64}, Length: {len(result_b64)}")

        result = b64encode(result_b64).decode()
        print(f"result: {result}, Length: {len(result)}")

        print("")

        return result

    def decrypt(self, encrypted_data: str) -> str | None:
        """Do decryption of input string, Returns non encrypted data."""
        print(f"DECRYPT: {encrypted_data}")

        encrypted_value = b64decode(encrypted_data.encode())[BLOCK_SIZE:]
        print(f"encrypted_value: {encrypted_value}")

        cipher = self._get_cipher()
        decryptor = cipher.decryptor()
        plain = decryptor.update(encrypted_value) + decryptor.finalize()
        plain = self._un_pad(plain)
        print(f"plain: {plain}")

        result = plain.decode()
        print(f"result: {result}")

        return result


email = os.environ.get(API_REQUEST_SERIAL_EMAIL, "email@email.com")
motor_unit_serial_number = os.environ.get(API_REQUEST_SERIAL_NUMBER, "ROB12345")

instance = AWSTokenGenerator(email)
encrypted_data_result = instance.encrypt(motor_unit_serial_number)
decrypted_data_result = instance.decrypt(encrypted_data_result)
