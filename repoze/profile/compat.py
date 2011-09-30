import sys

try:
    from StringIO import StringIO as BytesIO
except: # pragma: no cover
    from io import BytesIO

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3

if PY3: # pragma: no cover
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes
    long = int
else:
    string_types = basestring,
    integer_types = (int, long)
    text_type = unicode
    binary_type = str
    long = long

def bytes_(s, encoding='utf-8', errors='strict'):
    if isinstance(s, text_type): # pragma: no cover
        return s.encode(encoding, errors)
    return s

def text_(s, encoding='utf-8', errors='strict'):
    if isinstance(s, binary_type):
        return s.decode(encoding, errors)
    return s # pragma: no cover

try:
    from urllib.parse import parse_qs
except ImportError:
    try:
        from urlparse import parse_qs
    except ImportError: # pragma: no cover
        from cgi import parse_qs

try: # pragma: no cover
    import cProfile as profile # pragma: no cover
except ImportError: # pragma: no cover
    import profile # pragma: no cover

try: 
    from StringIO import StringIO
except: # pragma: no cover
    from io import StringIO
    

if PY3: # pragma: no cover
    from urllib.parse import quote as url_quote
else:
    from urllib import quote as url_quote

