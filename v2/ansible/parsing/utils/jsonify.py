# FIXME: header

try:
    import json
except ImportError:
    import simplejson as json

def jsonify(result, format=False):
    ''' format JSON output (uncompressed or uncompressed) '''

    if result is None:
        return "{}"
    result2 = result.copy()
    for key, value in result2.items():
        if type(value) is str:
            result2[key] = value.decode('utf-8', 'ignore')

    indent = None
    if format:
        indent = 4

    try:
        return json.dumps(result2, sort_keys=True, indent=indent, ensure_ascii=False)
    except UnicodeDecodeError:
        return json.dumps(result2, sort_keys=True, indent=indent)

