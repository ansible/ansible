.. _netconf_plugins:

Netconf Plugins
===============

.. contents::
   :local:
   :depth: 2

Netconf plugins are abstractions over the Netconf interface to network devices. They provide a standard interface
for Ansible to execute tasks on those network devices.

These plugins generally correspond one-to-one to network device platforms. The appropriate netconf plugin will
thus be automatically loaded based on the ``ansible_network_os`` variable. If the platform supports standard
Netconf implementation as defined in the Netconf RFC specification the ``default`` netconf plugin will be used.
In case if the platform supports propriety Netconf RPC's in that case the interface can be defined in platform
specific netconf plugin.

.. _enabling_netconf:

Adding netconf plugins
-------------------------

You can extend Ansible to support other network devices by dropping a custom plugin into the ``netconf_plugins`` directory.

.. _using_netconf:

Using netconf plugins
------------------------

The netconf plugin to use is determined automatically from the ``ansible_network_os`` variable. There should be no reason to override this functionality.

Most netconf plugins can operate without configuration. A few have additional options that can be set to impact how
tasks are translated into netconf commands. A ncclient device specific handler name can be set in the netconf plugin
or else the value of ``default`` is used as per ncclient device handler.


Plugins are self-documenting. Each plugin should document its configuration options.

.. _netconf_plugin_list:

Plugin list
-----------

You can use ``ansible-doc -t netconf -l`` to see the list of available plugins.
Use ``ansible-doc -t netconf <plugin name>`` to see detailed documentation and examples.


.. toctree:: :maxdepth: 1
    :glob:

    netconf/*


.. seealso::

   :ref:`Ansible for Network Automation<network_guide>`
       An overview of using Ansible to automate networking devices.
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible-network IRC chat channel
