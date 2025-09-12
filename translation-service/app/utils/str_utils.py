import re

def sanitize_filename(file: str) -> str:
    return re.sub(r"[^\w\d\-_.]", "_", file)


def canonize_str(s: str) -> str:
    # strip, lowercase, normalize, remove whitespace/punctuation for safety
    return "".join(filter(str.isalnum, s)).lower()