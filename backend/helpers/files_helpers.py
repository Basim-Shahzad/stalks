import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'csv', 'pdf'}

def get_extension(filename):
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return None

def is_allowed(filename):
    return get_extension(filename) in ALLOWED_EXTENSIONS

def secure_it(filename):
    return secure_filename(filename)
