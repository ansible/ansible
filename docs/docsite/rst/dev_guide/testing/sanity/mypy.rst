mypy
====

The ``mypy`` static type checker is used to check the following code against each Python version supported by the controller:

 * ``lib/ansible/``
 * ``test/lib/ansible_test/_internal/``

Additionally, the following code is checked against Python versions supported only on managed nodes:

 * ``lib/ansible/modules/``
 * ``lib/ansible/module_utils/``

See `the mypy documentation https://mypy.readthedocs.io/en/stable/`_ for additional details.
