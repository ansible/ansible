.. _terminal_plugins:

Terminal Plugins
================

.. contents::
   :local:
   :depth: 2

Terminal plugins provides low level abstraction APIs and options for setting
the remote host terminal after initial login.

These plugins generally correspond one-to-one to network device platforms. The appropriate terminal plugin will
thus be automatically loaded based on the ``ansible_network_os`` variable.

.. _enabling_terminal:

Adding terminal plugins
-----------------------

You can extend Ansible to support other network devices by dropping a custom plugin into the ``terminal_plugins`` directory.

.. _using_terminal:

Using terminal plugins
----------------------

The terminal plugin to use is determined automatically from the ``ansible_network_os`` variable. There should be no reason to override this functionality.

Most terminal plugins can operate without configuration. A few have additional options that can be set to impact how
tasks are translated into CLI commands and how the the response from target host is parsed.

Plugins are self-documenting. Each plugin should document its configuration options.

.. _terminal_plugin_list:

Plugin list
-----------

You can use ``ansible-doc -t terminal -l`` to see the list of available plugins.
Use ``ansible-doc -t terminal <plugin name>`` to see detailed documentation and examples.


.. toctree:: :maxdepth: 1
    :glob:

    terminal/*


.. seealso::

   :ref:`Ansible for Network Automation<network_guide>`
       An overview of using Ansible to automate networking devices.
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible-network IRC chat channel
