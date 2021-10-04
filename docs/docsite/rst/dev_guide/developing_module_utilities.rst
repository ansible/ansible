.. _developing_module_utilities:

*************************************
Using and developing module utilities
*************************************

Ansible provides a number of module utilities, or snippets of shared code, that
provide helper functions you can use when developing your own modules. The
``basic.py`` module utility provides the main entry point for accessing the
Ansible library, and all Python Ansible modules must import something from
``ansible.module_utils``. A common option is to import ``AnsibleModule``:

.. code-block:: python

  from ansible.module_utils.basic import AnsibleModule

The ``ansible.module_utils`` namespace is not a plain Python package: it is
constructed dynamically for each task invocation, by extracting imports and
resolving those matching the namespace against a :ref:`search path <ansible_search_path>` derived from the
active configuration.

To reduce the maintenance burden in a collection or in local modules, you can extract
duplicated code into one or more module utilities and import them into your modules. For example, if you have your own custom modules that import a ``my_shared_code`` library, you can place that into a ``./module_utils/my_shared_code.py`` file like this::

  from ansible.module_utils.my_shared_code import MySharedCodeClient

When you run ``ansible-playbook``, Ansible will merge any files in your local ``module_utils`` directories into the ``ansible.module_utils`` namespace in the order defined by the :ref:`Ansible search path <ansible_search_path>`.

Naming and finding module utilities
===================================

You can generally tell what a module utility does from its name and/or its location. Generic utilities (shared code used by many different kinds of modules) live in the main ansible/ansible codebase, in the ``common`` subdirectory or in the root directory of ``lib/ansible/module_utils``. Utilities used by a particular set of modules generally live in the same collection as those modules. For example:

* ``lib/ansible/module_utils/urls.py`` contains shared code for parsing URLs
* ``openstack.cloud.plugins.module_utils.openstack.py`` contains utilities for modules that work with OpenStack instances
* ``ansible.netcommon.plugins.module_utils.network.common.config.py`` contains utility functions for use by networking modules

Following this pattern with your own module utilities makes everything easy to find and use.

.. _standard_mod_utils:

Standard module utilities
=========================

Ansible ships with an extensive library of ``module_utils`` files. You can find the module utility source code in the ``lib/ansible/module_utils`` directory under your main Ansible path. We describe the most widely used utilities below. For more details on any specific module utility, please see the `source code for module_utils <https://github.com/ansible/ansible/tree/devel/lib/ansible/module_utils>`_.

.. include:: shared_snippets/licensing.txt

- ``api.py`` - Supports generic API modules
- ``basic.py`` - General definitions and helper utilities for Ansible modules
- ``common/dict_transformations.py`` - Helper functions for dictionary transformations
- ``common/file.py`` - Helper functions for working with files
- ``common/text/`` - Helper functions for converting and formatting text
- ``common/parameters.py`` - Helper functions for dealing with module parameters
- ``common/sys_info.py`` - Functions for getting distribution and platform information
- ``common/validation.py`` - Helper functions for validating module parameters against a module argument spec
- ``facts/`` - Directory of utilities for modules that return facts. See `PR 23012 <https://github.com/ansible/ansible/pull/23012>`_ for more information
- ``json_utils.py`` - Utilities for filtering unrelated output around module JSON output, like leading and trailing lines
- ``powershell/`` - Directory of definitions and helper functions for Windows PowerShell modules
- ``pycompat24.py`` - Exception workaround for Python 2.4
- ``service.py`` - Utilities to enable modules to work with Linux services (placeholder, not in use)
- ``six/__init__.py`` - Bundled copy of the `Six Python library <https://pypi.org/project/six/>`_ to aid in writing code compatible with both Python 2 and Python 3
- ``splitter.py`` - String splitting and manipulation utilities for working with Jinja2 templates
- ``urls.py`` - Utilities for working with http and https requests

Several commonly-used utilities migrated to collections in Ansible 2.10, including:

- ``ismount.py`` migrated to ``ansible.posix.plugins.module_utils.mount.py`` - Single helper function that fixes os.path.ismount
- ``known_hosts.py`` migrated to ``community.general.plugins.module_utils.known_hosts.py`` - utilities for working with known_hosts file

For a list of migrated content with destination collections, see https://github.com/ansible/ansible/blob/devel/lib/ansible/config/ansible_builtin_runtime.yml.
