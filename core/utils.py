from cryptography.fernet import Fernet
from pyqueen import TimeKit

def encrypt(text, key):
    cipher = Fernet(key.encode('utf-8'))
    return cipher.encrypt(text.encode('utf-8')).decode('utf-8')


def decrypt(text, key):
    cipher = Fernet(key.encode('utf-8'))
    return cipher.decrypt(text).decode('utf-8')


def print_log(text):
    tk = TimeKit()
    print(tk.int2str(tk.now)+' '+str(text))