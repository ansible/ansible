Sanity Tests » import
=====================

All python imports in ``lib/ansible/modules/`` and ``lib/ansible/module_utils/`` which are not from the python standard library
must be imported in a try/except ImportError block.
