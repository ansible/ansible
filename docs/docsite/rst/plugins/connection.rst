.. contents:: Topics


Connection Plugins
------------------

Connection plugins allow Ansible to connect to the target hosts so it can execute tasks on them. Ansible ships with many connection plugins, but only one can be used per host at a time.

By default, Ansible ships with several plugins. The most commonly used are the 'paramiko' SSH, native ssh (just called 'ssh'), and 'local' connection types.  All of these can be used in playbooks and with /usr/bin/ansible to decide how you want to talk to remote machines.  

The basics of these connection types are covered in the :doc:`../intro_getting_started` section.  



.. _ssh_plugins:

ssh Plugins
+++++++++++

Because ssh is the default protocol used in system administration and the protocol most used in Ansible, ssh options are included in the command line tools. See :doc:`../ansible-playbook` for more details.

.. _enabling_connection:

Enabling Connection Plugins
+++++++++++++++++++++++++++

You can extend Ansible to support other transports (such as SNMP or message bus) by dropping a custom plugin
into the ``connection_plugins`` directory.


.. _using_connection:

Using Connection Plugins
++++++++++++++++++++++++

The transport can be changed via :doc:`configuration <../config>`, in the command line (``-c``, ``--connection``), as a keyword (:ref:`connection`)
in your play, or by setting the a connection variable (:ref:`ansible_connection`), most often in your inventory.
For example, for Windows machines you might want to use the :doc:`winrm <connection/winrm>` plugin.

Most connection plugins can operate with a minimum configuration. By default they use the :ref:`inventory_hostname` and defaults to find the target host.

Plugins are self-documenting. Each plugin should document its configuration options. The following are connection variables common to most connection plugins:

:ref:`ansible_host`
    The name of the host to connect to, if different from the :ref:`inventory_hostname`.
:ref:`ansible_port`
    The ssh port number, for :doc:`ssh <connection/ssh>` and :doc:`paramiko <connection/paramiko>` it defaults to 22.
:ref:`ansible_user`
    The default user name to use for log in. Most plugins default to the 'current user running Ansible'.

Each plugin might also have a specific version of a variable that overrides the general version. For example, :ref:`ansible_ssh_host` for the :doc:`ssh <connection/ssh>` plugin.

.. _connection_plugin_list:

Plugin List
+++++++++++

You can use ``ansible-doc -t connection -l`` to see the list of available plugins.
Use ``ansible-doc -t connection <plugin name>`` to see detailed documentation and examples.


.. toctree:: :maxdepth: 1
    :glob:

    connection/*


.. seealso::

   :doc:`../playbooks`
       An introduction to playbooks
   :doc:`callback`
       Ansible callback plugins
   :doc:`../playbooks_filters`
       Jinja2 filter plugins
   :doc:`../playbooks_tests`
       Jinja2 test plugins
   :doc:`../playbooks_lookups`
       Jinja2 lookup plugins
   :doc:`vars`
       Ansible vars plugins
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
