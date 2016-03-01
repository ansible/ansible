from voluptuous import ALLOW_EXTRA, Any, Required, Schema

option_schema = Schema(
    {
        Required('description'): Any(basestring, [basestring]),
        'required': bool,
        'choices': Any(list, basestring),
        'aliases': list,
        'version_added': Any(basestring, float)
    },
    extra=ALLOW_EXTRA
)

doc_schema = Schema(
    {
        Required('module'): basestring,
        'short_description': Any(basestring, [basestring]),
        'description': Any(basestring, [basestring]),
        'version_added': Any(basestring, float),
        'author': Any(None, basestring, [basestring]),
        'notes': Any(None, [basestring]),
        'requirements': [basestring],
        'options': Any(None, dict),
        'extends_documentation_fragment': Any(basestring, [basestring])
    },
    extra=ALLOW_EXTRA
)
