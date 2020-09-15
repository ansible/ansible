:orphan:

.. _testing_pep8:

*****
PEP 8
*****

.. contents:: Topics

`PEP 8`_ style guidelines are enforced by `pycodestyle`_ on all python files in the repository by default.

Running Locally
===============

The `PEP 8`_ check can be run locally with::


    ansible-test sanity --test pep8 [file-or-directory-path-to-check] ...



.. _PEP 8: https://www.python.org/dev/peps/pep-0008/
.. _pycodestyle: https://pypi.org/project/pycodestyle/
