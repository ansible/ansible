# Add the "intersphinx" extension
# this allows references to the Python Documentation
# from within our docs
extensions = [
    'sphinx.ext.intersphinx',
]
# Add mappings
intersphinx_mapping = {
    'py3': ('http://docs.python.org/3', None),
    'py2': ('http://docs.python.org/2', None),
}
