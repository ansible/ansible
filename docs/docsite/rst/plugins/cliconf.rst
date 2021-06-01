.. _cliconf_plugins:

Cliconf Plugins
===============

.. contents::
   :local:
   :depth: 2

Cliconf plugins are abstractions over the CLI interface to network devices. They provide a standard interface
for Ansible to execute tasks on those network devices.

These plugins generally correspond one-to-one to network device platforms. The appropriate cliconf plugin will
thus be automatically loaded based on the ``ansible_network_os`` variable.

.. _enabling_cliconf:

Adding cliconf plugins
-------------------------

You can extend Ansible to support other network devices by dropping a custom plugin into the ``cliconf_plugins`` directory.

.. _using_cliconf:

Using cliconf plugins
------------------------

The cliconf plugin to use is determined automatically from the ``ansible_network_os`` variable. There should be no reason to override this functionality.

Most cliconf plugins can operate without configuration. A few have additional options that can be set to impact how
tasks are translated into CLI commands.

Plugins are self-documenting. Each plugin should document its configuration options.

.. _cliconf_plugin_list:

Plugin list
-----------

You can use ``ansible-doc -t cliconf -l`` to see the list of available plugins.
Use ``ansible-doc -t cliconf <plugin name>`` to see detailed documentation and examples.


.. toctree:: :maxdepth: 1
    :glob:

    cliconf/*


.. seealso::

   :ref:`Ansible for Network Automation<network_guide>`
       An overview of using Ansible to automate networking devices.
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.libera.chat <https://libera.chat/>`_
       #ansible-network IRC chat channel
