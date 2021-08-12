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

The ``validate-modules`` tool has a `schema.py <https://github.com/ansible/ansible/blob/devel/test/lib/ansible_test/_util/controller/sanity/validate-modules/validate_modules/schema.py>`_ that is used to validate the YAML blocks, such as ``DOCUMENTATION`` and ``RETURNS``.


Codes
=====

============================================================   ==================   ====================   =========================================================================================
  **Error Code**                                                 **Type**             **Level**            **Sample Message**
------------------------------------------------------------   ------------------   --------------------   -----------------------------------------------------------------------------------------
  ansible-deprecated-module                                    Documentation        Error                  A module is deprecated and supposed to be removed in the current or an earlier Ansible version
  collection-deprecated-module                                 Documentation        Error                  A module is deprecated and supposed to be removed in the current or an earlier collection version
  ansible-deprecated-version                                   Documentation        Error                  A feature is deprecated and supposed to be removed in the current or an earlier Ansible version
  ansible-module-not-initialized                               Syntax               Error                  Execution of the module did not result in initialization of AnsibleModule
  collection-deprecated-version                                Documentation        Error                  A feature is deprecated and supposed to be removed in the current or an earlier collection version
  deprecated-date                                              Documentation        Error                  A date before today appears as ``removed_at_date`` or in ``deprecated_aliases``
  deprecation-mismatch                                         Documentation        Error                  Module marked as deprecated or removed in at least one of the filename, its metadata, or in DOCUMENTATION (setting DOCUMENTATION.deprecated for deprecation or removing all Documentation for removed) but not in all three places.
  doc-choices-do-not-match-spec                                Documentation        Error                  Value for "choices" from the argument_spec does not match the documentation
  doc-choices-incompatible-type                                Documentation        Error                  Choices value from the documentation is not compatible with type defined in the argument_spec
  doc-default-does-not-match-spec                              Documentation        Error                  Value for "default" from the argument_spec does not match the documentation
  doc-default-incompatible-type                                Documentation        Error                  Default value from the documentation is not compatible with type defined in the argument_spec
  doc-elements-invalid                                         Documentation        Error                  Documentation specifies elements for argument, when "type" is not ``list``.
  doc-elements-mismatch                                        Documentation        Error                  Argument_spec defines elements different than documentation does
  doc-missing-type                                             Documentation        Error                  Documentation doesn't specify a type but argument in ``argument_spec`` use default type (``str``)
  doc-required-mismatch                                        Documentation        Error                  argument in argument_spec is required but documentation says it is not, or vice versa
  doc-type-does-not-match-spec                                 Documentation        Error                  Argument_spec defines type different than documentation does
  documentation-error                                          Documentation        Error                  Unknown ``DOCUMENTATION`` error
  documentation-syntax-error                                   Documentation        Error                  Invalid ``DOCUMENTATION`` schema
  illegal-future-imports                                       Imports              Error                  Only the following ``from __future__`` imports are allowed: ``absolute_import``, ``division``, and ``print_function``.
  import-before-documentation                                  Imports              Error                  Import found before documentation variables. All imports must appear below ``DOCUMENTATION``/``EXAMPLES``/``RETURN``
  import-error                                                 Documentation        Error                  ``Exception`` attempting to import module for ``argument_spec`` introspection
  import-placement                                             Locations            Warning                Imports should be directly below ``DOCUMENTATION``/``EXAMPLES``/``RETURN``
  imports-improper-location                                    Imports              Error                  Imports should be directly below ``DOCUMENTATION``/``EXAMPLES``/``RETURN``
  incompatible-choices                                         Documentation        Error                  Choices value from the argument_spec is not compatible with type defined in the argument_spec
  incompatible-default-type                                    Documentation        Error                  Default value from the argument_spec is not compatible with type defined in the argument_spec
  invalid-argument-name                                        Documentation        Error                  Argument in argument_spec must not be one of 'message', 'syslog_facility' as it is used internally by Ansible Core Engine
  invalid-argument-spec                                        Documentation        Error                  Argument in argument_spec must be a dictionary/hash when used
  invalid-argument-spec-options                                Documentation        Error                  Suboptions in argument_spec are invalid
  invalid-documentation                                        Documentation        Error                  ``DOCUMENTATION`` is not valid YAML
  invalid-documentation-options                                Documentation        Error                  ``DOCUMENTATION.options`` must be a dictionary/hash when used
  invalid-examples                                             Documentation        Error                  ``EXAMPLES`` is not valid YAML
  invalid-extension                                            Naming               Error                  Official Ansible modules must have a ``.py`` extension for python modules or a ``.ps1`` for powershell modules
  invalid-module-schema                                        Documentation        Error                  ``AnsibleModule`` schema validation error
  invalid-removal-version                                      Documentation        Error                  The version at which a feature is supposed to be removed cannot be parsed (for collections, it must be a semantic version, see https://semver.org/)
  invalid-requires-extension                                   Naming               Error                  Module ``#AnsibleRequires -CSharpUtil`` should not end in .cs, Module ``#Requires`` should not end in .psm1
  missing-doc-fragment                                         Documentation        Error                  ``DOCUMENTATION`` fragment missing
  missing-existing-doc-fragment                                Documentation        Warning                Pre-existing ``DOCUMENTATION`` fragment missing
  missing-documentation                                        Documentation        Error                  No ``DOCUMENTATION`` provided
  missing-examples                                             Documentation        Error                  No ``EXAMPLES`` provided
  missing-gplv3-license                                        Documentation        Error                  GPLv3 license header not found
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
  no-log-needed                                                Parameters           Error                  Option name suggests that the option contains a secret value, while ``no_log`` is not specified for this option in the argument spec. If this is a false positive, explicitly set ``no_log=False``
  nonexistent-parameter-documented                             Documentation        Error                  Argument is listed in DOCUMENTATION.options, but not accepted by the module
  option-incorrect-version-added                               Documentation        Error                  ``version_added`` for new option is incorrect
  option-invalid-version-added                                 Documentation        Error                  ``version_added`` for option is not a valid version number
  parameter-invalid                                            Documentation        Error                  Argument in argument_spec is not a valid python identifier
  parameter-invalid-elements                                   Documentation        Error                  Value for "elements" is valid only when value of "type" is ``list``
  implied-parameter-type-mismatch                              Documentation        Error                  Argument_spec implies ``type="str"`` but documentation defines it as different data type
  parameter-type-not-in-doc                                    Documentation        Error                  Type value is defined in ``argument_spec`` but documentation doesn't specify a type
  parameter-alias-repeated                                     Parameters           Error                  argument in argument_spec has at least one alias specified multiple times in aliases
  parameter-alias-self                                         Parameters           Error                  argument in argument_spec is specified as its own alias
  parameter-documented-multiple-times                          Documentation        Error                  argument in argument_spec with aliases is documented multiple times
  parameter-list-no-elements                                   Parameters           Error                  argument in argument_spec "type" is specified as ``list`` without defining "elements"
  parameter-state-invalid-choice                               Parameters           Error                  Argument ``state`` includes ``get``, ``list`` or ``info`` as a choice.  Functionality should be in an ``_info`` or (if further conditions apply) ``_facts`` module.
  python-syntax-error                                          Syntax               Error                  Python ``SyntaxError`` while parsing module
  removal-version-must-be-major                                Documentation        Error                  According to the semantic versioning specification (https://semver.org/), the only versions in which features are allowed to be removed are major versions (x.0.0)
  return-syntax-error                                          Documentation        Error                  ``RETURN`` is not valid YAML, ``RETURN`` fragments missing  or invalid
  return-invalid-version-added                                 Documentation        Error                  ``version_added`` for return value is not a valid version number
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
  mutually_exclusive-type                                      Documentation        Error                  mutually_exclusive entry contains non-string value
  mutually_exclusive-collision                                 Documentation        Error                  mutually_exclusive entry has repeated terms
  mutually_exclusive-unknown                                   Documentation        Error                  mutually_exclusive entry contains option which does not appear in argument_spec (potentially an alias of an option?)
  required_one_of-type                                         Documentation        Error                  required_one_of entry contains non-string value
  required_one_of-collision                                    Documentation        Error                  required_one_of entry has repeated terms
  required_one_of-unknown                                      Documentation        Error                  required_one_of entry contains option which does not appear in argument_spec (potentially an alias of an option?)
  required_together-type                                       Documentation        Error                  required_together entry contains non-string value
  required_together-collision                                  Documentation        Error                  required_together entry has repeated terms
  required_together-unknown                                    Documentation        Error                  required_together entry contains option which does not appear in argument_spec (potentially an alias of an option?)
  required_if-is_one_of-type                                   Documentation        Error                  required_if entry has a fourth value which is not a bool
  required_if-requirements-type                                Documentation        Error                  required_if entry has a third value (requirements) which is not a list or tuple
  required_if-requirements-collision                           Documentation        Error                  required_if entry has repeated terms in requirements
  required_if-requirements-unknown                             Documentation        Error                  required_if entry's requirements contains option which does not appear in argument_spec (potentially an alias of an option?)
  required_if-unknown-key                                      Documentation        Error                  required_if entry's key does not appear in argument_spec (potentially an alias of an option?)
  required_if-key-in-requirements                              Documentation        Error                  required_if entry contains its key in requirements list/tuple
  required_if-value-type                                       Documentation        Error                  required_if entry's value is not of the type specified for its key
  required_by-collision                                        Documentation        Error                  required_by entry has repeated terms
  required_by-unknown                                          Documentation        Error                  required_by entry contains option which does not appear in argument_spec (potentially an alias of an option?)
  version-added-must-be-major-or-minor                         Documentation        Error                  According to the semantic versioning specification (https://semver.org/), the only versions in which features are allowed to be added are major and minor versions (x.y.0)
============================================================   ==================   ====================   =========================================================================================
