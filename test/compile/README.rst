Compile Tests
=============

Compile tests check source files for valid syntax on all supported python versions:

- 2.6
- 2.7
- 3.5
- 3.6

Tests are run with ``ansible-test compile``.
All versions are tested unless the ``--python`` option is used.
All ``*.py`` files are tested unless specific files are specified.
