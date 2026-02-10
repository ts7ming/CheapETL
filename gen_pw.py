import os
from pyqueen import DataSource
from cryptography.fernet import Fernet

# --------------------------  加密解码  --------------------------
def encrypt(text, key):
    cipher = Fernet(key.encode('utf-8'))
    return cipher.encrypt(text.encode('utf-8')).decode('utf-8')


def decrypt(text, key):
    cipher = Fernet(key.encode('utf-8'))
    return cipher.decrypt(text).decode('utf-8')

try:
    import settings
except ImportError:
    settings = None

ds_cfg = DataSource(**settings.DS_CONFIG) if hasattr(settings, 'DS_CONFIG') else None
SECRET_KEY = getattr(settings, 'SECRET_KEY', 'SECRET_KEY')


if __name__ == '__main__':
    pw = input('password:')
    pw = str(pw).strip()
    epw = encrypt(pw, SECRET_KEY)
    if decrypt(epw, SECRET_KEY) == pw:
        print(f'encrypt password: "{epw}"')
    else:
        print('校验失败')
