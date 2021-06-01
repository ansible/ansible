.. _httpapi_plugins:

Httpapi Plugins
===============

.. contents::
   :local:
   :depth: 2

Httpapi plugins tell Ansible how to interact with a remote device's HTTP-based API and execute tasks on the
device.

Each plugin represents a particular dialect of API. Some are platform-specific (Arista eAPI, Cisco NXAPI), while
others might be usable on a variety of platforms (RESTCONF).

.. _enabling_httpapi:

Adding httpapi plugins
-------------------------

You can extend Ansible to support other APIs by dropping a custom plugin into the ``httpapi_plugins`` directory. See :ref:`developing_plugins_httpapi` for details.

.. _using_httpapi:

Using httpapi plugins
------------------------

The httpapi plugin to use is determined automatically from the ``ansible_network_os`` variable.

Most httpapi plugins can operate without configuration. Additional options may be defined by each plugin.

Plugins are self-documenting. Each plugin should document its configuration options.


.. _httpapi_plugin_list:

Plugin List
-----------

You can use ``ansible-doc -t httpapi -l`` to see the list of available plugins.
Use ``ansible-doc -t httpapi <plugin name>`` to see detailed documentation and examples.


.. toctree:: :maxdepth: 1
    :glob:

    httpapi/*


.. seealso::

   :ref:`Ansible for Network Automation<network_guide>`
       An overview of using Ansible to automate networking devices.
   :ref:`Developing network modules<developing_modules_network>`
       How to develop network modules.
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.libera.chat <https://libera.chat/>`_
       #ansible-network IRC chat channel
