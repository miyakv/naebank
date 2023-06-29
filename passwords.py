import hashlib
import re


def encode(string):
    return str(hashlib.sha256(string.encode()).hexdigest())


def check_password(to_test, goal_hash):
    if str(hashlib.sha256(to_test.encode()).hexdigest()) == goal_hash:
        return True
    return False


def validate_password(password):
    if re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$', password) is None:
        return False
    return True
