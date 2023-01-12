.. _adjacent_yaml_doc:

*********************************
Adjacent YAML documentation files
*********************************

.. contents::
   :local:

YAML documentation for plugins
------------------------------
For most Ansible plugins, the documentation is in the same file as the code. This approach does not work for cases when:

  * Multiple plugins are defined in the same file, such as tests and filters.
  * Plugins are written in a language other than Python (modules).

These cases require plugins to provide documentation in an adjacent ``.py`` file. As of ansible-core 2.14, you can provide documentation as adjacent YAML files instead.
The format of a YAML documentation file is nearly identical to its Python equivalent, except it is pure YAML.


YAML format
-----------
In Python each section is a variable ``DOCUMENTATION = r""" ... """`` while in YAML it is a mapping key ``DOCUMENTATION: ...``.

Here is a longer example that shows documentation as embedded in a Python file:

.. code-block:: python

  DOCUMENTATION = r'''
    description: something
    options:
      option_name:
        description: describe this config option
        default: default value for this config option
        env:
          - name: NAME_OF_ENV_VAR
        ini:
          - section: section_of_ansible.cfg_where_this_config_option_is_defined
            key: key_used_in_ansible.cfg
        vars:
          - name: name_of_ansible_var
          - name: name_of_second_var
            version_added: X.x
        required: True/False
        type: boolean/float/integer/list/none/path/pathlist/pathspec/string/tmppath
        version_added: X.x
  '''

  EXAMPLES = r'''
    # TODO: write examples
  '''

This example shows the same documentation in YAML format:

.. code-block:: YAML

  DOCUMENTATION:
    description: something
    options:
      option_name:
        description: describe this config option
        default: default value for this config option
        env:
          - name: NAME_OF_ENV_VAR
        ini:
          - section: section_of_ansible.cfg_where_this_config_option_is_defined
            key: key_used_in_ansible.cfg
        vars:
          - name: name_of_ansible_var
          - name: name_of_second_var
            version_added: X.x
        required: True/False
        type: boolean/float/integer/list/none/path/pathlist/pathspec/string/tmppath
        version_added: X.x

  EXAMPLES: # TODO: write examples

As the examples above show, Python variables already contain YAML. The main change to use YAML documentation is to simply move the YAML out of such variables.

 Any adjacent YAML documentation files must be in the same directory as the plugin or module that they document. This means the documentation is available in any directory that contains the plugins or modules.


Supported plugin types
----------------------
YAML documentation is mainly intended for filters, tests and modules. While it is possible to use with other plugin types, Ansible always recommends having documentation in the same file as the code for most cases.

.. seealso::

   :ref:`list_of_collections`
       Browse existing collections, modules, and plugins
   :ref:`developing_api`
       Learn about the Python API for task execution
   :ref:`developing_inventory`
       Learn about how to develop dynamic inventory sources
   :ref:`developing_modules_general`
       Learn about how to write Ansible modules
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
   :ref:`communication_irc`
       How to join Ansible chat channels
