import secrets
import string

def generate_short_token(length=12):
    """Generate random alphanumeric token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

