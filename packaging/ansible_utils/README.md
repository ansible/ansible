# ansible_utils

Standalone distributions of selected `ansible-core` utilities, exposed under an
independent import namespace so third-party tooling can use them without
depending on the full `ansible-core` distribution.

The source is shared with `ansible-core`; this distribution simply repackages it
under the `ansible_utils` namespace. It can be installed alongside `ansible-core`
because it uses a different import path.

Two subpackages are provided:

- `ansible_utils.collection_loader` — resolve, discover, and load Ansible
  collections (the same code that ships as `ansible.utils.collection_loader`).
- `ansible_utils.doc_extractor` — read plugin documentation variables from
  Python source without importing the module (the same code that ships as
  `ansible.utils.doc_extractor`).

## Usage

Install the finder against one or more collection root paths, then discover
installed collections and read their metadata. Contents are enumerated with the
standard library (`importlib.resources` or `pkgutil`), which works through the
installed finder. A plugin's source can be read without importing it and passed
to the doc extractor.

```python
from importlib.resources import files

from ansible_utils.collection_loader import (
    install_finder,
    find_collection_paths,
    read_collection_manifest,
)
from ansible_utils.doc_extractor import ast_py_docs

# A collection root is a directory containing an `ansible_collections` package.
install_finder(["/path/to/collections"])

for path in find_collection_paths():
    namespace, name = path.parent.name, path.name
    meta = read_collection_manifest(path)
    print(namespace, name, meta and meta.get("version"))

    # Enumerate a plugin type and read a plugin's docs without importing it.
    modules = files(f"ansible_collections.{namespace}.{name}.plugins.modules")
    for entry in modules.glob("**/*.py"):
        docs = ast_py_docs(entry)
```

## License

GPL-3.0-or-later. See `COPYING`. Portions vendored from CPython are covered by
`PSF-license.txt`.
