.. _appendix_module_utilities:

**************************
Appendix: Module Utilities
**************************

Ansible provides a number of module utilities, or snippets of shared code, that
provide helper functions you can use when developing your own modules. The
``basic.py`` module utility provides the main entry point for accessing the
Ansible library, and all Python Ansible modules must import something from
``ansible.module_utils``. A common option is to import ``AnsibleModule``::

  from ansible.module_utils.basic import AnsibleModule

The ``ansible.module_utils`` namespace is not a plain Python package: it is
constructed dynamically for each task invocation, by extracting imports and
resolving those matching the namespace against a search path derived from the
active configuration.

If you need to share Python code between some of your own local modules, you can use Ansible's ``module_utils`` directories for this. When you run ``ansible-playbook``, Ansible will merge any files in the local ``module_utils`` directory into the ``ansible.module_utils`` namespace. For example, if you have your own custom modules that import a ``my_shared_code`` library, you can place that into a ``./module_utils/my_shared_code.py`` file in the root location where your playbook lives, and then import it in your modules like so::

  from ansible.module_utils.my_shared_code import MySharedCodeClient

Your custom ``module_utils`` directories can live in the root directory of your playbook, or in the individual role directories, or in the directories specified by the ``ANSIBLE_MODULE_UTILS`` configuration setting.

Naming and finding module utilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ansible uses namespacing to organize module utilities. We store generic
utilities in the ``common`` subdirectory or in the root directory. For example,
the shared code for parsing URLs is in ``lib/ansible/module_utils/urls.py``.
Code files with a more specific purpose live in more specific
directories. For example, modules related to EMC live in ``lib/ansible/modules/storage/emc/``
and the module utilities related to EMC live in ``lib/ansible/module_utils/storage/emc/``.
Following this pattern with your own module utilities makes everything easy to find and use.

.. _standard_mod_utils:

Standard module utilities
~~~~~~~~~~~~~~~~~~~~~~~~~

Ansible ships with a comprehensive library of ``module_utils`` files.
You can find the module
utility source code in the ``./lib/ansible/module_utils`` directory under
your main Ansible path. Most module utilities have names that describe their
functions - for example, ``openstack.py`` contains utilities for modules that work with Openstack instances. We've described the most widely-used utilities below. For more details on any specific module utility,
please see the `source code <https://github.com/ansible/ansible/tree/devel/lib/ansible/module_utils>`_.

.. include:: shared_snippets/licensing.txt

- ``basic.py`` - General definitions and helper utilities for Ansible modules.
- ``facts/`` - Folder containing helper functions for modules that return facts. See `PR 23012 <https://github.com/ansible/ansible/pull/23012>`_ for more information.
- ``ismount.py`` - Contains single helper function that fixes os.path.ismount
- ``known_hosts.py`` - utilities for working with known_hosts file
- ``network/common/config.py`` - Configuration utility functions for use by networking modules
- ``network/common/netconf.py`` - Definitions and helper functions for modules that use Netconf transport.
- ``network/common/parsing.py`` - Definitions and helper functions for Network modules.
- ``network/common/network.py`` - Functions for running commands on networking devices
- ``network/common/utils.py`` - Defines commands and comparison operators and other utilises for use in networking modules
- ``powershell/` - Utilities for working with Microsoft Windows clients
- ``pycompat24.py`` - Exception workaround for Python 2.4.
- ``service.py`` - Contains utilities to enable modules to work with Linux services (placeholder, not in use).
- ``shell.py`` - Functions to allow modules to create shells and work with shell commands
- ``six/__init__.py`` - Bundled copy of the `Six Python library <https://pythonhosted.org/six/>`_ to aid in writing code compatible with both Python 2 and Python 3.
- ``splitter.py`` - String splitting and manipulation utilities for working with Jinja2 templates
- ``urls.py`` - Utilities for working with http and https requests
