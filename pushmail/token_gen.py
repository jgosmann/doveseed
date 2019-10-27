import os

from .registration import Token


def gen_secure_token():
    while True:
        yield Token(os.urandom(16))
