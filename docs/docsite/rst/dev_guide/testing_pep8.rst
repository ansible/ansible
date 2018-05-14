*****
PEP 8
*****

.. contents:: Topics

`PEP 8`_ style guidelines are enforced by `pycodestyle`_ on all python files in the repository by default.

Current Rule Set
================

By default all files are tested using the current rule set.
All `PEP 8`_ tests are executed, except those listed in the `current ignore list`_.

.. warning: Updating the Rule Set

   Changes to the Rule Set need approval from the Core Team, and must be done via the `Testing Working Group <https://github.com/ansible/community/blob/master/meetings/README.md>`_.

Legacy Rule Set
===============

Files which are listed in the `legacy file list`_ are tested using the legacy rule set.

All `PEP 8`_ tests are executed, except those listed in the `current ignore list`_ or `legacy ignore list`_.

Files listed in the legacy file list which pass the current rule set will result in an error.

This is intended to prevent regressions on style guidelines for files which pass the more stringent current rule set.

Skipping Tests
==============

Files listed in the `skip list`_ are not tested by `pycodestyle`_.

Removed Files
=============

Files which have been removed from the repository must be removed from the legacy file list and the skip list.

Running Locally
===============

The `PEP 8`_ check can be run locally with::


    ./test/runner/ansible-test sanity --test pep8 [file-or-directory-path-to-check] ...



.. _PEP 8: https://www.python.org/dev/peps/pep-0008/
.. _pycodestyle: https://pypi.org/project/pycodestyle/
.. _current ignore list: https://github.com/ansible/ansible/blob/devel/test/sanity/pep8/current-ignore.txt
.. _legacy file list: https://github.com/ansible/ansible/blob/devel/test/sanity/pep8/legacy-files.txt
.. _legacy ignore list: https://github.com/ansible/ansible/blob/devel/test/sanity/pep8/legacy-ignore.txt
.. _skip list: https://github.com/ansible/ansible/blob/devel/test/sanity/pep8/skip.txt
