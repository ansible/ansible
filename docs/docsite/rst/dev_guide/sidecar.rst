.. _adjacent_yaml_doc:

**********************************
Alternate YAML documentation files
**********************************

.. contents::
   :local:

For reasons
-----------
Most plugins in Ansible contain the documentation in the same file as the code, this is very convenient for many reasons but does not work well for all cases:

  * when multiple plugins are defined in the same file (like tests and filters).
  * when the plugins are written in a language other than Python (modules). Until now we required an adjacent ``.py`` file to contain the documentation

Since ansible-core 2.14 we have added the ability to have adjacent YAML files to contain the documenbtation.
The format of these files is almost identical to the documentation in existing Python files, the major difference, it is pure YAML.


The format
-----------
The short of it, in Python you had each section as a Python variable ``DOCUMENTATION = r""" ....`` while in YAML it is just a mapping key ``DOCUMENTATION: ``.

Longer example, this would be the documentation as embeded in the Python file:

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

While this is the same documentation in a YAML file:

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

As you can see the changes are minor as the Python variables already contained YAML, so the main change is moving away from the YAML being contained in such variables.

These 'adjacent YAML' files need to be in the same directory as the plugin/module that they document and as such can appear in any directory the plugins/modules appear in.


Supported plugin types
----------------------
This was mainly developed for filters, tests and modules as mentioned above, there is no reason it cannot be applied to other plugin types but we currently do not see a use case and having the documentations in the same file is till a big advantage for those other plugin types.

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
