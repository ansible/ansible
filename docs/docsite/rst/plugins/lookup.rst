.. _lookup_plugins:

Lookup Plugins
==============

.. contents::
   :local:
   :depth: 2

Lookup plugins allow Ansible to access data from outside sources.
This can include reading the filesystem in addition to contacting external datastores and services.
Like all templating, these plugins are evaluated on the Ansible control machine, not on the target/remote.

The data returned by a lookup plugin is made available using the standard templating system in Ansible,
and are typically used to load variables or templates with information from those systems.

Lookups are an Ansible-specific extension to the Jinja2 templating language.

.. note::
   - Lookups are executed with a working directory relative to the role or play,
     as opposed to local tasks, which are executed relative the executed script.
   - Since Ansible version 1.9, you can pass wantlist=True to lookups to use in Jinja2 template "for" loops.
   - Lookup plugins are an advanced feature; to best leverage them you should have a good working knowledge of how to use Ansible plays.

.. warning::
   - Some lookups pass arguments to a shell. When using variables from a remote/untrusted source, use the `|quote` filter to ensure safe usage.


.. _enabling_lookup:

Enabling lookup plugins
-----------------------

You can activate a custom lookup by either dropping it into a ``lookup_plugins`` directory adjacent to your play, inside a role, or by putting it in one of the lookup directory sources configured in :ref:`ansible.cfg <ansible_configuration_settings>`.


.. _using_lookup:

Using lookup plugins
--------------------

Lookup plugins can be used anywhere you can use templating in Ansible: in a play, in variables file, or in a Jinja2 template for the :ref:`template <template_module>` module.

.. code-block:: YAML+Jinja

  vars:
    file_contents: "{{lookup('file', 'path/to/file.txt')}}"

Lookups are an integral part of loops. Wherever you see ``with_``, the part after the underscore is the name of a lookup.
This is also the reason most lookups output lists and take lists as input; for example, ``with_items`` uses the :ref:`items <items_lookup>` lookup::

  tasks:
    - name: count to 3
      debug: msg={{item}}
      with_items: [1, 2, 3]

You can combine lookups with :ref:`playbooks_filters`, :ref:`playbooks_tests` and even each other to do some complex data generation and manipulation. For example::

  tasks:
    - name: valid but useless and over complicated chained lookups and filters
      debug: msg="find the answer here:\n{{ lookup('url', 'https://google.com/search/?q=' + item|urlencode)|join(' ') }}"
      with_nested:
        - "{{lookup('consul_kv', 'bcs/' + lookup('file', '/the/question') + ', host=localhost, port=2000')|shuffle}}"
        - "{{lookup('sequence', 'end=42 start=2 step=2')|map('log', 4)|list)}}"
        - ['a', 'c', 'd', 'c']

.. versionadded:: 2.6

You can now control how errors behave in all lookup plugins by setting ``errors`` to ``ignore``, ``warn``, or ``strict``. The default setting is ``strict``, which causes the task to fail. For example:

To ignore errors::

    - name: file doesnt exist, but i dont care .. file plugin itself warns anyways ...
      debug: msg="{{ lookup('file', '/idontexist', errors='ignore') }}"

.. code-block:: ansible-output

    [WARNING]: Unable to find '/idontexist' in expected paths (use -vvvvv to see paths)

    ok: [localhost] => {
        "msg": ""
    }


To get a warning instead of a failure::

    - name: file doesnt exist, let me know, but continue
      debug: msg="{{ lookup('file', '/idontexist', errors='warn') }}"

.. code-block:: ansible-output

    [WARNING]: Unable to find '/idontexist' in expected paths (use -vvvvv to see paths)

    [WARNING]: An unhandled exception occurred while running the lookup plugin 'file'. Error was a <class 'ansible.errors.AnsibleError'>, original message: could not locate file in lookup: /idontexist

    ok: [localhost] => {
        "msg": ""
    }


Fatal error (the default)::

    - name: file doesnt exist, FAIL (this is the default)
      debug: msg="{{ lookup('file', '/idontexist', errors='strict') }}"

.. code-block:: ansible-output

    [WARNING]: Unable to find '/idontexist' in expected paths (use -vvvvv to see paths)

    fatal: [localhost]: FAILED! => {"msg": "An unhandled exception occurred while running the lookup plugin 'file'. Error was a <class 'ansible.errors.AnsibleError'>, original message: could not locate file in lookup: /idontexist"}


.. _query:

Invoking lookup plugins with ``query``
--------------------------------------

.. versionadded:: 2.5

In Ansible 2.5, a new jinja2 function called ``query`` was added for invoking lookup plugins. The difference between ``lookup`` and ``query`` is largely that ``query`` will always return a list.
The default behavior of ``lookup`` is to return a string of comma separated values. ``lookup`` can be explicitly configured to return a list using ``wantlist=True``.

This was done primarily to provide an easier and more consistent interface for interacting with the new ``loop`` keyword, while maintaining backwards compatibility with other uses of ``lookup``.

The following examples are equivalent:

.. code-block:: jinja

    lookup('dict', dict_variable, wantlist=True)

    query('dict', dict_variable)

As demonstrated above the behavior of ``wantlist=True`` is implicit when using ``query``.

Additionally, ``q`` was introduced as a shortform of ``query``:

.. code-block:: jinja

    q('dict', dict_variable)


.. _lookup_plugins_list:

Plugin list
-----------

You can use ``ansible-doc -t lookup -l`` to see the list of available plugins. Use ``ansible-doc -t lookup <plugin name>`` to see specific documents and examples.


.. toctree:: :maxdepth: 1
    :glob:

    lookup/*

.. seealso::

   :ref:`about_playbooks`
       An introduction to playbooks
   :ref:`inventory_plugins`
       Ansible inventory plugins
   :ref:`callback_plugins`
       Ansible callback plugins
   :ref:`playbooks_filters`
       Jinja2 filter plugins
   :ref:`playbooks_tests`
       Jinja2 test plugins
   :ref:`playbooks_lookups`
       Jinja2 lookup plugins
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
