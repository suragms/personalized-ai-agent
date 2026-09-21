#!/usr/bin/env python
"""Generate a secure SECRET_KEY for Django production use."""
import secrets
import string


def generate_secret_key(length=50):
    """Generate a cryptographically secure random secret key."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


if __name__ == '__main__':
    key = generate_secret_key()
    print("\n" + "="*60)
    print("Generated Django SECRET_KEY:")
    print("="*60)
    print(key)
    print("="*60)
    print("\nAdd this to your .env file:")
    print(f"SECRET_KEY={key}")
    print("\n⚠️  Keep this secret and never commit it to version control!")
    print("="*60 + "\n")
