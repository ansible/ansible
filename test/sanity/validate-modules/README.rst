validate-modules
================

Python program to help test or validate Ansible modules.

Originally developed by Matt Martz (@sivel)

Usage
~~~~~

.. code:: shell

    cd /path/to/ansible/source
    source hacking/env-setup
    test/sanity/validate-modules/validate-modules /path/to/modules

Help
~~~~

.. code:: shell

    usage: validate-modules [-h] [-w] [--exclude EXCLUDE] modules

    positional arguments:
      modules            Path to module or module directory

    optional arguments:
      -h, --help         show this help message and exit
      -w, --warnings     Show warnings
      --exclude EXCLUDE  RegEx exclusion pattern

Current Validations
===================

Modules
~~~~~~~

Errors
^^^^^^

#. Interpreter line is not ``#!/usr/bin/python``
#. ``main()`` not at the bottom of the file
#. Module does not import ``ansible.module_utils.basic``
#. Missing ``DOCUMENTATION``
#. Documentation is invalid YAML
#. Invalid schema for ``DOCUMENTATION``
#. Missing ``EXAMPLES``
#. Invalid Python Syntax
#. Tabbed indentation
#. Use of ``sys.exit()`` instead of ``exit_json`` or ``fail_json``
#. Missing GPLv3 license header in module
#. PowerShell module missing ``WANT_JSON``
#. PowerShell module missing ``POWERSHELL_COMMON``
#. New modules have the correct ``version_added``
#. New arguments have the correct ``version_added``
#. Modules should not import requests, instead use ``ansible.module_utils.urls``
#. Missing ``RETURN`` for new modules
#. Use of ``type()`` for type comparison instead of ``isinstance()``

Warnings
^^^^^^^^

#. Try/Except ``HAS_`` expression missing
#. Missing ``RETURN`` for existing modules
#. ``import json`` found
#. Module contains duplicate globals from basic.py

Module Directories (Python Packages)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Missing ``__init__.py``
