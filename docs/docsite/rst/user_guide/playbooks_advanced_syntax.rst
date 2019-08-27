.. _playbooks_advanced_syntax:

***************
Advanced Syntax
***************

The advanced YAML syntax examples on this page give you more control over the data placed in YAML files used by Ansible. You can find additional information about Python-specific YAML in the official `PyYAML Documentation <https://pyyaml.org/wiki/PyYAMLDocumentation#YAMLtagsandPythontypes>`_.

.. contents::
   :local:

.. _unsafe_strings:

Unsafe or Raw Strings
=====================

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

.. _anchors_and_aliases:

YAML anchors and aliases: sharing variable values
=================================================

`YAML anchors and aliases <https://yaml.org/spec/1.2/spec.html#id2765878>`_ help you define, maintain, and use shared variable values in a flexible way.
You define an anchor with ``&``, then refer to it using an alias, denoted with ``*``. Here's an example that sets three values with an anchor, uses two of those values with an alias, and overrides the third value::

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

Anchors and aliases also let you share complex sets of variable values, including nested variables. If you have one variable value that includes another variable value, you can define them separately::

      vars:
        webapp_version: 1.0
        webapp_custom_name: ToDo_App-1.0

This is inefficient and, at scale, means more maintenance. To incorporate the version value in the name, you can use an anchor in ``app_version`` and an alias in ``custom_name``::

      vars:
        webapp:
            version: &my_version 1.0
            custom_name:
                - "ToDo_App"
                - *my_version

Now, you can re-use the value of ``app_version`` within the value of  ``custom_name`` and use the output in a template::

    ---
    - name: Using values nested inside dictionary
      hosts: localhost
      vars:
        webapp:
            version: &my_version 1.0
            custom_name:
                - "ToDo_App"
                - *my_version
      tasks:
      - name: Using Anchor value
        debug:
            msg: My app is called "{{ webapp.custom_name | join('-') }}".

You've anchored the value of ``version`` with the ``&my_version`` anchor, and re-used it with the ``*my_version`` alias. Anchors and aliases let you access nested values inside dictionaries.

.. seealso::

   :ref:`playbooks_variables`
       All about variables
   `User Mailing List <https://groups.google.com/group/ansible-project>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
