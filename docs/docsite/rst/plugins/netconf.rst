.. _netconf_plugins:

Netconf Plugins
===============

.. contents::
   :local:
   :depth: 2

.. warning::

	Links on this page may not point to the most recent versions of plugins. In preparation for the release of 2.10, many plugins and modules have migrated to Collections on  `Ansible Galaxy <https://galaxy.ansible.com>`_. For the current development status of Collections and FAQ see `Ansible Collections Community Guide <https://github.com/ansible-collections/overview/blob/master/README.rst>`_.

Netconf plugins are abstractions over the Netconf interface to network devices. They provide a standard interface for Ansible to execute tasks on those network devices.

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

These plugins have migrated to a collection. Updates on where to find and how to use them will be coming soon.


.. seealso::

   :ref:`Ansible for Network Automation<network_guide>`
       An overview of using Ansible to automate networking devices.
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible-network IRC chat channel
