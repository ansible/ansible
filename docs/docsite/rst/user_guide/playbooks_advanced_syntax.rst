.. _playbooks_advanced_syntax:

Advanced Syntax
===============

.. contents:: Topics

This page describes advanced YAML syntax that enables you to have more control over the data placed in YAML files used by Ansible.

.. _yaml_tags_and_python_types:

YAML tags and Python types
``````````````````````````

The documentation covered here is an extension of the documentation that can be found in the `PyYAML Documentation <https://pyyaml.org/wiki/PyYAMLDocumentation#YAMLtagsandPythontypes>`_

.. _unsafe_strings:

Unsafe or Raw Strings
~~~~~~~~~~~~~~~~~~~~~

Ansible provides an internal data type for declaring variable values as "unsafe". This means that the data held within the variables value should be treated as unsafe preventing unsafe character substitution and information disclosure.

Jinja2 contains functionality for escaping, or telling Jinja2 to not template data by means of functionality such as ``{% raw %} ... {% endraw %}``, however this uses a more comprehensive implementation to ensure that the value is never templated.

Using YAML tags, you can also mark a value as "unsafe" by using the ``!unsafe`` tag such as:

.. code-block:: yaml

    ---
    my_unsafe_variable: !unsafe 'this variable has {{ characters that should not be treated as a jinja2 template'

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


Sharing variable values with YAML anchors and aliases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to share variable values across tasks, `YAML anchors and aliases <https://yaml.org/spec/1.2/spec.html#id2765878>`_ help you define, maintain, and use those values in a flexible way.
You define an anchor with ``&``, then refer to it using an alias, denoted with ``*``.

Here's an example that sets three values with an anchor, uses two of those values with an alias, and overrides the third value::

    ---
    ...
    vars:
        app1:
            jvm: &jvm_opts
                opts: '-Xms1G -Xmx2G'
                port: 1000
                path: /usr/lib/app1
        app2:
            jvm:
                <<: *jvm_opts
                path: /usr/lib/app2
    ...

Here, ``app1`` and ``app2`` share the values for ``opts`` and ``port`` using the anchor ``&jvm_opts`` and the alias ``*jvm_opts``.
The value for ``path`` is merged by ``<<`` or `merge operator <https://yaml.org/type/merge.html>`_.

Anchors and aliases let you share complex sets of variable values, including nested variables.

Let us assume you have playbook::

      vars:
        webapp:
            app: 1.0
            custom: ToDo_App-1.0

Now, you want to re-use existing value of ``app`` value in ``custom`` value::

    ---
    - name: Using values nested inside dictionary
      hosts: localhost
      vars:
        webapp:
            app_version: &my_version 1.0
            custom_version:
                - "ToDo_App"
                - *my_version
      tasks:
      - name: Using Anchor value
        debug:
            msg: "{{ webapp.custom_version | join('-') }}"

Here, you can anchor 'app_version' value using ``&my_version`` and re-use later as ``*my_version``.
This way you can access nested values inside dictionaries.


.. seealso::

   :doc:`playbooks_variables`
       All about variables
   `User Mailing List <https://groups.google.com/group/ansible-project>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
