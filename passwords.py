import hashlib


def encode(string):
    return str(hashlib.sha256(string.encode()).hexdigest())


def check_password(to_test, goal_hash):
    if str(hashlib.sha256(to_test.encode()).hexdigest()) == goal_hash:
        return True
    return False
