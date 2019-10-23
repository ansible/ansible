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

============================================================   ==================   ====================   =========================================================================================
  **Error Code**                                                 **Type**             **Level**            **Sample Message**
------------------------------------------------------------   ------------------   --------------------   -----------------------------------------------------------------------------------------
  ansible-module-not-initialized                               Syntax               Error                  Execution of the module did not result in initialization of AnsibleModule
  deprecation-mismatch                                         Documentation        Error                  Module marked as deprecated or removed in at least one of the filename, its metadata, or in DOCUMENTATION (setting DOCUMENTATION.deprecated for deprecation or removing all Documentation for removed) but not in all three places.
  doc-choices-do-not-match-spec                                Documentation        Error                  Value for "choices" from the argument_spec does not match the documentation
  doc-choices-incompatible-type                                Documentation        Error                  Choices value from the documentation is not compatible with type defined in the argument_spec
  doc-default-does-not-match-spec                              Documentation        Error                  Value for "default" from the argument_spec does not match the documentation
  doc-default-incompatible-type                                Documentation        Error                  Default value from the documentation is not compatible with type defined in the argument_spec
  doc-missing-type                                             Documentation        Error                  Documentation doesn't specify a type but argument in ``argument_spec`` use default type (``str``)
  doc-type-does-not-match-spec                                 Documentation        Error                  Argument_spec defines type different than documentation does
  documentation-error                                          Documentation        Error                  Unknown ``DOCUMENTATION`` error
  documentation-syntax-error                                   Documentation        Error                  Invalid ``DOCUMENTATION`` schema
  illegal-future-imports                                       Imports              Error                  Only the following ``from __future__`` imports are allowed: ``absolute_import``, ``division``, and ``print_function``.
  import-before-documentation                                  Imports              Error                  Import found before documentation variables. All imports must appear below ``DOCUMENTATION``/``EXAMPLES``/``RETURN``/``ANSIBLE_METADATA``
  import-error                                                 Documentation        Error                  ``Exception`` attempting to import module for ``argument_spec`` introspection
  import-placement                                             Locations            Warning                Imports should be directly below ``DOCUMENTATION``/``EXAMPLES``/``RETURN``/``ANSIBLE_METADATA`` for legacy modules
  imports-improper-location                                    Imports              Error                  Imports should be directly below ``DOCUMENTATION``/``EXAMPLES``/``RETURN``/``ANSIBLE_METADATA``
  incompatible-choices                                         Documentation        Error                  Choices value from the argument_spec is not compatible with type defined in the argument_spec
  incompatible-default-type                                    Documentation        Error                  Default value from the argument_spec is not compatible with type defined in the argument_spec
  invalid-argument-spec                                        Documentation        Error                  Argument in argument_spec must be a dictionary/hash when used
  invalid-argument-spec-options                                Documentation        Error                  Suboptions in argument_spec are invalid
  invalid-documentation                                        Documentation        Error                  ``DOCUMENTATION`` is not valid YAML
  invalid-documentation-options                                Documentation        Error                  ``DOCUMENTATION.options`` must be a dictionary/hash when used
  invalid-examples                                             Documentation        Error                  ``EXAMPLES`` is not valid YAML
  invalid-extension                                            Naming               Error                  Official Ansible modules must have a ``.py`` extension for python modules or a ``.ps1`` for powershell modules
  invalid-metadata-status                                      Documentation        Error                  ``ANSIBLE_METADATA.status`` of deprecated or removed can't include other statuses
  invalid-metadata-type                                        Documentation        Error                  ``ANSIBLE_METADATA`` was not provided as a dict, YAML not supported, Invalid ``ANSIBLE_METADATA`` schema
  invalid-module-schema                                        Documentation        Error                  ``AnsibleModule`` schema validation error
  invalid-requires-extension                                   Naming               Error                  Module ``#AnsibleRequires -CSharpUtil`` should not end in .cs, Module ``#Requires`` should not end in .psm1
  last-line-main-call                                          Syntax               Error                  Call to ``main()`` not the last line (or ``removed_module()`` in the case of deprecated & docs only modules)
  metadata-changed                                             Documentation        Error                  ``ANSIBLE_METADATA`` cannot be changed in a point release for a stable branch
  missing-doc-fragment                                         Documentation        Error                  ``DOCUMENTATION`` fragment missing
  missing-existing-doc-fragment                                Documentation        Warning                Pre-existing ``DOCUMENTATION`` fragment missing
  missing-documentation                                        Documentation        Error                  No ``DOCUMENTATION`` provided
  missing-examples                                             Documentation        Error                  No ``EXAMPLES`` provided
  missing-gplv3-license                                        Documentation        Error                  GPLv3 license header not found
  missing-if-name-main                                         Syntax               Error                  Next to last line is not ``if __name__ == "__main__":``
  missing-main-call                                            Syntax               Error                  Did not find a call to ``main()`` (or ``removed_module()`` in the case of deprecated & docs only modules)
  missing-metadata                                             Documentation        Error                  No ``ANSIBLE_METADATA`` provided
  missing-module-utils-basic-import                            Imports              Warning                Did not find ``ansible.module_utils.basic`` import
  missing-module-utils-import-csharp-requirements              Imports              Error                  No ``Ansible.ModuleUtils`` or C# Ansible util requirements/imports found
  missing-powershell-interpreter                               Syntax               Error                  Interpreter line is not ``#!powershell``
  missing-python-doc                                           Naming               Error                  Missing python documentation file
  missing-python-interpreter                                   Syntax               Error                  Interpreter line is not ``#!/usr/bin/python``
  missing-return                                               Documentation        Error                  No ``RETURN`` documentation provided
  missing-return-legacy                                        Documentation        Warning                No ``RETURN`` documentation provided for legacy module
  missing-suboption-docs                                       Documentation        Error                  Argument in argument_spec has sub-options but documentation does not define sub-options
  module-incorrect-version-added                               Documentation        Error                  Module level ``version_added`` is incorrect
  module-invalid-version-added                                 Documentation        Error                  Module level ``version_added`` is not a valid version number
  module-utils-specific-import                                 Imports              Error                  ``module_utils`` imports should import specific components, not ``*``
  multiple-utils-per-requires                                  Imports              Error                  ``Ansible.ModuleUtils`` requirements do not support multiple modules per statement
  multiple-csharp-utils-per-requires                           Imports              Error                  Ansible C# util requirements do not support multiple utils per statement
  no-default-for-required-parameter                            Documentation        Error                  Option is marked as required but specifies a default. Arguments with a default should not be marked as required
  nonexistent-parameter-documented                             Documentation        Error                  Argument is listed in DOCUMENTATION.options, but not accepted by the module
  option-incorrect-version-added                               Documentation        Error                  ``version_added`` for new option is incorrect
  option-invalid-version-added                                 Documentation        Error                  ``version_added`` for new option is not a valid version number
  parameter-invalid                                            Documentation        Error                  Argument in argument_spec is not a valid python identifier
  parameter-invalid-elements                                   Documentation        Error                  Value for "elements" is valid only when value of "type" is ``list``
  implied-parameter-type-mismatch                              Documentation        Error                  Argument_spec implies ``type="str"`` but documentation defines it as different data type
  parameter-type-not-in-doc                                    Documentation        Error                  Type value is defined in ``argument_spec`` but documentation doesn't specify a type
  python-syntax-error                                          Syntax               Error                  Python ``SyntaxError`` while parsing module
  return-syntax-error                                          Documentation        Error                  ``RETURN`` is not valid YAML, ``RETURN`` fragments missing  or invalid
  subdirectory-missing-init                                    Naming               Error                  Ansible module subdirectories must contain an ``__init__.py``
  try-except-missing-has                                       Imports              Warning                Try/Except ``HAS_`` expression missing
  undocumented-parameter                                       Documentation        Error                  Argument is listed in the argument_spec, but not documented in the module
  unidiomatic-typecheck                                        Syntax               Error                  Type comparison using ``type()`` found. Use ``isinstance()`` instead
  unknown-doc-fragment                                         Documentation        Warning                Unknown pre-existing ``DOCUMENTATION`` error
  use-boto3                                                    Imports              Error                  ``boto`` import found, new modules should use ``boto3``
  use-fail-json-not-sys-exit                                   Imports              Error                  ``sys.exit()`` call found. Should be ``exit_json``/``fail_json``
  use-module-utils-urls                                        Imports              Error                  ``requests`` import found, should use ``ansible.module_utils.urls`` instead
  use-run-command-not-os-call                                  Imports              Error                  ``os.call`` used instead of ``module.run_command``
  use-run-command-not-popen                                    Imports              Error                  ``subprocess.Popen`` used instead of ``module.run_command``
  use-short-gplv3-license                                      Documentation        Error                  GPLv3 license header should be the :ref:`short form <copyright>` for new modules
============================================================   ==================   ====================   =========================================================================================
