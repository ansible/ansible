Advanced Syntax
===============

.. contents:: Topics

This page describes advanced YAML syntax that enables you to have more control over the data placed in YAML files used by Ansible.

.. _yaml_tags_and_python_types:

YAML tags and Python types
``````````````````````````

The documentation covered here is an extension of the documentation that can be found in the `PyYAML Documentation <http://pyyaml.org/wiki/PyYAMLDocumentation#YAMLtagsandPythontypes>`_

.. _unsafe_strings:

Unsafe or Raw Strings
~~~~~~~~~~~~~~~~~~~~~

As of Ansible 2.0, there is an internal data type for declaring variable values as "unsafe". This means that the data held within the variables value should be treated as unsafe preventing unsafe character subsitition and information disclosure.

Jinja2 contains functionality for escaping, or telling Jinja2 to not template data by means of functionality such as ``{% raw %} ... {% endraw %}``, however this uses a more comprehensive implementation to ensure that the value is never templated.

Using YAML tags, you can also mark a value as "unsafe" by using the ``!unsafe`` tag such as::

    ---
    my_unsafe_variable: !unsafe 'this variable has {{ characters that shouldn't be treated as a jinja2 template'

In a playbook, this may look like::

    ---
    hosts: all
    vars:
        my_unsafe_variable: !unsafe 'unsafe value'
    tasks:
        ...

For complex variables such as hashes or arrays, ``!unsafe`` should be used on the individual elements such as::

    ---
    my_unsafe_array:
        - !unsafe 'unsafe element'
        - 'safe element'

    my_unsafe_hash:
        unsafe_key: !unsafe 'unsafe value'

 

.. seealso::

   :doc:`playbooks_variables`
       All about variables
   `User Mailing List <http://groups.google.com/group/ansible-project>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


