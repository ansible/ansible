.. _filter_plugins:

Filter plugins
==============

.. contents::
   :local:
   :depth: 2

Filter plugins manipulate data. With the right filter you can extract a particular value, transform data types and formats, perform mathematical calculations, split and concatenate strings, insert dates and times, and do much more.  Ansible uses the :ref:`standard filters <jinja2:builtin-filters>` shipped with Jinja2 and adds some specialized filter plugins. You can :ref:`create custom Ansible filters as plugins <developing_filter_plugins>`.

.. _enabling_filter:

Enabling filter plugins
-----------------------

You can add a custom filter plugin by dropping it into a ``filter_plugins`` directory adjacent to your play, inside a role, or by putting it in one of the filter plugin directory sources configured in :ref:`ansible.cfg <ansible_configuration_settings>`.

.. _using_filter:

Using filter plugins
--------------------

You can use filters anywhere you can use templating in Ansible: in a play, in variables file, or in a Jinja2 template for the :ref:`template <template_module>` module. For more information on using filter plugins, see :ref:`playbooks_filters`.  Filters can return any type of data, but if you want to always return a boolean (``True`` or ``False``) you should be looking at a test instead.

.. code-block:: YAML+Jinja

  vars:
     yaml_string: "{{ some_variable|to_yaml }}"

Filters are the preferred way to manipulate data in Ansible, you can identify a filter because it is normally preceded by a ``|``, with the expression on the left of it being the first input of the filter. Additional parameters may be passed into the filter itself as you would to most programming functions. These parameters can be either ``positional`` (passed in order) or ``named`` (passed as key=value pairs). When passing both types, positional arguments should go first.

.. code-block:: YAML+Jinja

   passing_positional: {{ (x == 32) | ternary('x is 32', 'x is not 32') }}
   passing_extra_named_parameters: {{ some_variable | to_yaml(indent=8, width=1337) }}
   passing_both: {{ some_variable| ternary('true value', 'false value', none_val='NULL') }}

In the documentation, filters will always have a C(_input) option that corresponds to the expression to the left of c(|). A C(positional:) field in the documentation will show which options are positional and in which order they are required.


Plugin list
-----------

You can use ``ansible-doc -t filter -l`` to see the list of available plugins. Use ``ansible-doc -t filter <plugin name>`` to see specific documents and examples.


.. seealso::

   :ref:`about_playbooks`
       An introduction to playbooks
   :ref:`inventory_plugins`
       Inventory plugins
   :ref:`callback_plugins`
       Callback plugins
   :ref:`test_plugins`
      Test plugins
   :ref:`lookup_plugins`
       Lookup plugins
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   :ref:`communication_irc`
       How to join Ansible chat channels
