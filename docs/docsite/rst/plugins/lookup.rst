.. contents:: Topics


Lookup Plugins
--------------

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

Enabling Lookup Plugins
+++++++++++++++++++++++

You can activate a custom lookup by either dropping it into a ``lookup_plugins`` directory adjacent to your play, inside a role, or by putting it in one of the lookup directory sources configured in :doc:`ansible.cfg <../config>`.


.. _using_lookup:

Using Lookup Plugins
++++++++++++++++++++

Lookup plugins can be used anywhere you can use templating in Ansible: in a play, in variables file, or in a Jinja2 template for the :doc:`template <../template_module>` module.

.. code-block:: yaml

  vars:
    file_contents: "{{lookup('file', 'path/to/file.txt')}}"

Lookups are an integral part of loops. Wherever you see ``with_``, the part after the underscore is the name of a lookup.
This is also the reason most lookups output lists and take lists as input; for example, ``with_items`` uses the :doc:`items <lookup/items>` lookup:

.. code-block:: yaml

  tasks:
    - name: count to 3
      debug: msg={{item}}
      with_items: [1, 2, 3]

You can combine lookups with :doc:`../playbooks_filters`, :doc:`../playbooks_tests` and even each other to do some complex data generation and maniplulation. For example:

.. code-block:: yaml

  tasks:
    - name: valid but useless and over complicated chained lookups and filters
      debug: msg="find the answer here:\n{{ lookup('url', 'http://google.com/search/?q=' + item|urlencode)|join(' ') }}"
      with_nested:
        - "{{lookup('consul_kv', 'bcs/' + lookup('file', '/the/question') + ', host=localhost, port=2000')|shuffle}}"
        - "{{lookup('sequence', 'end=42 start=2 step=2')|map('log', 4)|list)}}"
        - ['a', 'c', 'd', 'c']


.. _lookup_plugins_list:

Plugin List
+++++++++++

You can use ``ansible-doc -t lookup -l`` to see the list of available plugins. Use ``ansible-doc -t lookup <plugin name>`` to see specific documents and examples.


.. toctree:: :maxdepth: 1
    :glob:

    lookup/*

.. seealso::

   :doc:`../playbooks`
       An introduction to playbooks
   :doc:`inventory`
       Ansible inventory plugins
   :doc:`callback`
       Ansible callback plugins
   :doc:`../playbooks_filters`
       Jinja2 filter plugins
   :doc:`../playbooks_tests`
       Jinja2 test plugins
   :doc:`../playbooks_lookups`
       Jinja2 lookup plugins
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
