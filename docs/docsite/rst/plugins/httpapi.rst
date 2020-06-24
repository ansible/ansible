.. _httpapi_plugins:

Httpapi Plugins
===============

.. contents::
   :local:
   :depth: 2

.. warning::

	Links on this page may not point to the most recent versions of plugins. In preparation for the release of 2.10, many plugins and modules have migrated to Collections on  `Ansible Galaxy <https://galaxy.ansible.com>`_. For the current development status of Collections and FAQ see `Ansible Collections Community Guide <https://github.com/ansible-collections/overview/blob/main/README.rst>`_.

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


The following sample playbook shows the httpapi plugin for an Arista network device, assuming an inventory variable set as ``ansible_network_os=eos`` for the httpapi plugin to trigger off:

.. code-block:: yaml

  - hosts: leaf01
    connection: httpapi
    gather_facts: false
    tasks:

      - name: type a simple arista command
        eos_command:
          commands:
            - show version | json
        register: command_output

      - name: print command output to terminal window
        debug:
          var: command_output.stdout[0]["version"]

See the full working example at https://github.com/network-automation/httpapi.

.. _httpapi_plugin_list:

Plugin List
-----------

These plugins have migrated to a collection. Updates on where to find and how to use them will be coming soon.

.. seealso::

   :ref:`Ansible for Network Automation<network_guide>`
       An overview of using Ansible to automate networking devices.
   :ref:`Developing network modules<developing_modules_network>`
       How to develop network modules.
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible-network IRC chat channel
