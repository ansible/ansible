.. contents:: Topics


Lookup Plugins
--------------

Lookup plugins allow access of data in Ansible from outside sources,
this can include reading the filesystem but also contacting external datastores and services.
Like all templating, these plugins are evaluated on the Ansible control machine NOT on the target/remote.

These values are then made available using the standard templating system in Ansible,
and are typically used to load variables or templates with information from those systems.

Lookups are an Ansible specific extension to the Jinja2 templating language.

.. note::
   - Lookups are executed with a working directory relative to the role or play,
     as opposed to local tasks which are executed relative the executed script.
   - Since 1.9 you can pass wantlist=True to lookups to use in Jinja2 template "for" loops.
   - This is considered an advanced feature, you should try to feel comfortable with Ansible plays before incorporating them.


.. warning::
   - Some lookups pass arguments to a shell. When using variables from a remote/untrusted source, use the `|quote` filter to ensure safe usage.


.. _enabling_lookup:

Enabling Lookup Plugins
+++++++++++++++++++++++

You can activate a custom lookup by either dropping it into a ``lookup_plugins`` directory adjacent to your play or inside a role
or by putting it in one of the lookup directory sources configured in :doc:`ansible.cfg <../config>`.


.. _using_lookup:

Using Lookup Plugins
++++++++++++++++++++

Basically you can use them anywhere you can use templating in Ansible, in a play, vars file and, of course,
in a Jinja2 template for the :doc:`template <../template_module>` module.

.. code-block:: yaml

  vars:
    file_contents: "{{lookup('file', 'path/to/file.txt')}}"

Lookups are also an integral part of loops, whereever you see ``with_`` the part after the underscore is the name of a lookup.
This is also the reason most lookups output lists and take lists as input.
i.e. ``with_items`` uses the :doc:`items <lookup/items>` lookup:

.. code-block:: yaml

  tasks:
    - name: count to 3
      debug: msg={{item}}
      with_items: [1, 2, 3]

You can combine them with :doc:`../playbooks_filters`, :doc:`../playbooks_tests` and even each other to do some complex data generation and maniplulation:

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

You can use ``ansible-doc -t lookup -l`` to see the list of available plugins,
use ``ansible-doc -t lookup <plugin name>`` to see specific documents and examples.


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
