Sanity Tests » import
=====================

All Python imports in ``lib/ansible/modules/`` and ``lib/ansible/module_utils/`` which are not from the Python standard library
must be imported in a try/except ImportError block.
