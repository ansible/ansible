from __future__ import annotations

import os
from importlib.resources import files

from ansible.utils.collection_loader import (
    install_finder,
    find_collection_paths,
    read_collection_manifest,
)
from ansible.utils.doc_extractor import ast_py_docs

install_finder([os.path.dirname(__file__)])

expected = [
    (
        'ns',
        'col',
        '1.2.3',
        {
            'DOCUMENTATION': {
                'module': 'hello',
                'short_description': 'Hello test module',
                'description': 'Hello test module.',
                'options': {
                    'name': {
                        'description': 'Name to say hello to.',
                        'type': 'str'
                    }
                },
                'author': ['Ansible Core Team']
            }
        },
    ),
]
found = []
for path in find_collection_paths():
    namespace, name = path.parent.name, path.name
    meta = read_collection_manifest(path)
    version = meta.get("version") if meta else '*'
    modules = files(f"ansible_collections.{namespace}.{name}.plugins.modules")
    for entry in modules.glob("**/*.py"):
        docs = ast_py_docs(entry)
        found.append((namespace, name, version, docs))

assert found == expected
