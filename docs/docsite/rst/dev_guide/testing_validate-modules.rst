****************
validate-modules
****************

.. contents:: Topics

Python program to help test or validate Ansible modules.

``validate-modules`` is one of the ``ansible-test`` Sanity Tests, see :doc:`testing_sanity` for more information.

Originally developed by Matt Martz (@sivel)


Usage
=====

.. code:: shell

    cd /path/to/ansible/source
    source hacking/env-setup
    ansible-test sanity --test validate-modules

Help
====

.. code:: shell

    usage: validate-modules [-h] [-w] [--exclude EXCLUDE] [--arg-spec]
                            [--base-branch BASE_BRANCH] [--format {json,plain}]
                            [--output OUTPUT]
                            modules [modules ...]

    positional arguments:
      modules               Path to module or module directory

    optional arguments:
      -h, --help            show this help message and exit
      -w, --warnings        Show warnings
      --exclude EXCLUDE     RegEx exclusion pattern
      --arg-spec            Analyze module argument spec
      --base-branch BASE_BRANCH
                            Used in determining if new options were added
      --format {json,plain}
                            Output format. Default: "plain"
      --output OUTPUT       Output location, use "-" for stdout. Default "-"


Extending validate-modules
==========================

The ``validate-modules`` tool has a `schema.py <https://github.com/ansible/ansible/blob/devel/test/sanity/validate-modules/schema.py>`_ that is used to validate the YAML blocks, such as ``DOCUMENTATION`` and ``RETURNS``.


Codes
=====

Errors
------

=========   ===================
  code      sample message
---------   -------------------
  **1xx**   **Locations**
  101       Interpreter line is not ``#!/usr/bin/python``
  102       Interpreter line is not ``#!powershell``
  103       Did not find a call to ``main()``
  104       Call to ``main()`` not the last line
  105       GPLv3 license header not found
  106       Import found before documentation variables. All imports must appear below
            ``DOCUMENTATION``/``EXAMPLES``/``RETURN``/``ANSIBLE_METADATA``
  107       Imports should be directly below ``DOCUMENTATION``/``EXAMPLES``/``RETURN``/``ANSIBLE_METADATA``
  ..
---------   -------------------
  **2xx**   **Imports**
  201       Did not find a ``module_utils`` import
  203       ``requests`` import found, should use ``ansible.module_utils.urls`` instead
  204       ``boto`` import found, new modules should use ``boto3``
  205       ``sys.exit()`` call found. Should be ``exit_json``/``fail_json``
  206       ``WANT_JSON`` not found in module
  207       ``REPLACER_WINDOWS`` not found in module
  208       ``module_utils`` imports should import specific components, not ``*``
  209       Only the following ``from __future__`` imports are allowed:
            ``absolute_import``, ``division``, and ``print_function``.
  ..
---------   -------------------
  **3xx**   **Documentation**
  301       No ``DOCUMENTATION`` provided
  302       ``DOCUMENTATION`` is not valid YAML
  303       ``DOCUMENTATION`` fragment missing
  304       Unknown ``DOCUMENTATION`` error
  305       Invalid ``DOCUMENTATION`` schema
  306       Module level ``version_added`` is not a valid version number
  307       Module level ``version_added`` is incorrect
  308       ``version_added`` for new option is not a valid version number
  309       ``version_added`` for new option is incorrect
  310       No ``EXAMPLES`` provided
  311       ``EXAMPLES`` is not valid YAML
  312       No ``RETURN`` documentation provided
  313       ``RETURN`` is not valid YAML
  314       No ``ANSIBLE_METADATA`` provided
  315       ``ANSIBLE_METADATA`` is not valid YAML
  316       Invalid ``ANSIBLE_METADATA`` schema
  317       option is marked as required but specifies a default.
            Arguments with a default should not be marked as required
  318       Module deprecated, but DOCUMENTATION.deprecated is missing
  319       ``RETURN`` fragments missing  or invalid
  ..
---------   -------------------
  **4xx**   **Syntax**
  401       Python ``SyntaxError`` while parsing module
  402       Indentation contains tabs
  403       Type comparison using ``type()`` found. Use ``isinstance()`` instead
  ..
---------   -------------------
  **5xx**   **Naming**
  501       Official Ansible modules must have a ``.py`` extension for python
            modules or a ``.ps1`` for powershell modules
  502       Ansible module subdirectories must contain an ``__init__.py``
  503       Missing python documentation file
=========   ===================

Warnings
--------

=========   ===================
  code      sample message
---------   -------------------
  **1xx**   **Locations**
  107       Imports should be directly below ``DOCUMENTATION``/``EXAMPLES``/``RETURN``/``ANSIBLE_METADATA`` for legacy modules
  ..
---------   -------------------
  **2xx**   **Imports**
  208       ``module_utils`` imports should import specific components for legacy module, not ``*``
  291       Try/Except ``HAS_`` expression missing
  292       Did not find ``ansible.module_utils.basic`` import
  ..
---------   -------------------
  **3xx**   **Documentation**
  312       No ``RETURN`` documentation provided for legacy module
  391       Unknown pre-existing ``DOCUMENTATION`` error
  392       Pre-existing ``DOCUMENTATION`` fragment missing
=========   ===================
