:orphan:

.. _testing_validate-modules:

****************
validate-modules
****************

.. contents:: Topics

Python program to help test or validate Ansible modules.

``validate-modules`` is one of the ``ansible-test`` Sanity Tests, see :ref:`testing_sanity` for more information.

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

The ``validate-modules`` tool has a `schema.py <https://github.com/ansible/ansible/blob/devel/test/lib/ansible_test/_data/sanity/validate-modules/validate_modules/schema.py>`_ that is used to validate the YAML blocks, such as ``DOCUMENTATION`` and ``RETURNS``.


Codes
=====

Errors
------

============================================================   ===================
  **Error Code**                                               **Sample Message**
------------------------------------------------------------   -------------------
  missing-python-interpreter                                   Interpreter line is not ``#!/usr/bin/python``
  missing-powershell-interpreter                               Interpreter line is not ``#!powershell``
  missing-main-call                                            Did not find a call to ``main()`` (or ``removed_module()`` in the case of deprecated & docs only modules)
  last-line-main-call                                          Call to ``main()`` not the last line (or ``removed_module()`` in the case of deprecated & docs only modules)
  missing-gplv3-license                                        GPLv3 license header not found
  import-before-documentation                                  Import found before documentation variables. All imports must appear below
                                                               ``DOCUMENTATION``/``EXAMPLES``/``RETURN``/``ANSIBLE_METADATA``
  imports-improper-location                                    Imports should be directly below ``DOCUMENTATION``/``EXAMPLES``/``RETURN``/``ANSIBLE_METADATA``
  use-short-gplv3-license                                      GPLv3 license header should be the :ref:`short form <copyright>` for new modules
  missing-if-name-main                                         Next to last line is not ``if __name__ == "__main__":``
  ..
------------------------------------------------------------   -------------------
  **Imports**
  missing-module-utils-import                                  Did not find a ``module_utils`` import
  use-module-utils-urls                                        ``requests`` import found, should use ``ansible.module_utils.urls`` instead
  use-boto3                                                    ``boto`` import found, new modules should use ``boto3``
  use-fail-json-not-sys-exit                                   ``sys.exit()`` call found. Should be ``exit_json``/``fail_json``
  missing-module-utils-import-c#                               No ``Ansible.ModuleUtils`` or C# Ansible util requirements/imports found
  module-utils-specific-import                                 ``module_utils`` imports should import specific components, not ``*``
  illegal-future-imports                                       Only the following ``from __future__`` imports are allowed:
                                                               ``absolute_import``, ``division``, and ``print_function``.
  multiple-utils-per-requires                                  ``Ansible.ModuleUtils`` requirements do not support multiple modules per statement
  multiple-utils-per-requires                                  Ansible C# util requirements do not support multiple utils per statement
  use-run-command-not-popen                                    ``subprocess.Popen`` used instead of ``module.run_command``
  use-run-command-not-os-call                                  ``os.call`` used instead of ``module.run_command``
  ..
------------------------------------------------------------   -------------------
  **Documentation**
  missing-documentation                                        No ``DOCUMENTATION`` provided
  invalid-documentation                                        ``DOCUMENTATION`` is not valid YAML
  documentation-syntax-error                                   Invalid ``DOCUMENTATION`` schema
  missing-doc-fragment                                         ``DOCUMENTATION`` fragment missing
  documentation-error                                          Unknown ``DOCUMENTATION`` error
  module-invalid-version-added                                 Module level ``version_added`` is not a valid version number
  module-incorrect-version-added                               Module level ``version_added`` is incorrect
  option-invalid-version-added                                 ``version_added`` for new option is not a valid version number
  option-incorrect-version-added                               ``version_added`` for new option is incorrect
  missing-examples                                             No ``EXAMPLES`` provided
  invalid-examples                                             ``EXAMPLES`` is not valid YAML
  missing-return                                               No ``RETURN`` documentation provided
  return-syntax-error                                          ``RETURN`` is not valid YAML, ``RETURN`` fragments missing  or invalid
  missing-metadata                                             No ``ANSIBLE_METADATA`` provided
  invalid-metadata-type                                        ``ANSIBLE_METADATA`` was not provided as a dict, YAML not supported, Invalid ``ANSIBLE_METADATA`` schema
  no-default-for-required-parameter                            Option is marked as required but specifies a default.
                                                               Arguments with a default should not be marked as required
  deprecation-mismatch                                         Module marked as deprecated or removed in at least one of the filename, its metadata, or
                                                               In DOCUMENTATION (setting DOCUMENTATION.deprecated for deprecation or removing all
                                                               Documentation for removed) but not in all three places.
  invalid-documentation-options                                ``DOCUMENTATION.options`` must be a dictionary/hash when used
  import-error                                                 ``Exception`` attempting to import module for ``argument_spec`` introspection
  undocumented-parameter                                       Argument is listed in the argument_spec, but not documented in the module
  nonexistent-parameter-documented                             Argument is listed in DOCUMENTATION.options, but not accepted by the module
  doc-default-does-not-match-spec                              Value for "default" from the argument_spec does not match the documentation
  doc-type-does-not-match-spec                                 Argument_spec defines type different than documentation does
  doc-choices-do-not-match-spec                                Value for "choices" from the argument_spec does not match the documentation
  doc-default-incompatible-type                                Default value from the documentation is not compatible with type defined in the argument_spec
  doc-choices-incompatible-type                                Choices value from the documentation is not compatible with type defined in the argument_spec
  incompatible-default-type                                    Default value from the argument_spec is not compatible with type defined in the argument_spec
  incompatible-choices                                         Choices value from the argument_spec is not compatible with type defined in the argument_spec
  invalid-argument-spec                                        Argument in argument_spec must be a dictionary/hash when used
  invalid-module-schema                                        ``AnsibleModule`` schema validation error
  invalid-metadata-status                                      ``ANSIBLE_METADATA.status`` of deprecated or removed can't include other statuses
  metadata-changed                                             ``ANSIBLE_METADATA`` cannot be changed in a point release for a stable branch
  parameter-type-does-not-match-doc                            Argument_spec implies type="str" but documentation defines it as different data type
  parameter-type-does-not-match-doc                            Type value is defined in ``argument_spec`` but documentation doesn't specify a type
  parameter-invalid                                            Argument in argument_spec is not a valid python identifier
  doc-missing-type                                             Documentation doesn't specify a type but argument in ``argument_spec`` use default type (``str``)
  parameter-invalid-elements                                   Value for "elements" is valid only when value of "type" is ``list``
  missing-subption-docs                                        Argument in argument_spec has sub-options but documentation does not define sub-options
  invalid-argument-spec-options                                Suboptions in argument_spec are invalid
  ..
------------------------------------------------------------   -------------------
  **Syntax**
  python-syntax-error                                          Python ``SyntaxError`` while parsing module
  unidiomatic-typecheck                                        Type comparison using ``type()`` found. Use ``isinstance()`` instead
  ..
------------------------------------------------------------   -------------------
  **Naming**
  invalid-extension                                            Official Ansible modules must have a ``.py`` extension for python
                                                               Modules or a ``.ps1`` for powershell modules
  invalid-requires-extension                                   Module ``#Requires`` should not end in .psm1
  invalid-requires-extension                                   Module ``#AnsibleRequires -CSharpUtil`` should not end in .cs
  subdirectory-missing-init                                    Ansible module subdirectories must contain an ``__init__.py``
  missing-python-doc                                           Missing python documentation file
============================================================   ===================

Warnings
--------

============================================================   ===================
  Code
------------------------------------------------------------   -------------------
  **Locations**
  import-placement                                             Imports should be directly below ``DOCUMENTATION``/``EXAMPLES``/``RETURN``/``ANSIBLE_METADATA`` for legacy modules
  ..
------------------------------------------------------------   -------------------
  **Imports**
  try-except-missing-has                                       Try/Except ``HAS_`` expression missing
  missing-module-utils-basic-import                            Did not find ``ansible.module_utils.basic`` import
  ..
------------------------------------------------------------   -------------------
  **Documentation**
  missing-return                                               No ``RETURN`` documentation provided for legacy module
  unknown-doc-fragment                                         Unknown pre-existing ``DOCUMENTATION`` error
  missing-doc-fragment                                         Pre-existing ``DOCUMENTATION`` fragment missing
============================================================   ===================
