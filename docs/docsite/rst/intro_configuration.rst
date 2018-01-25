Configuration
-------------

.. contents:: Topics


This topic describes how to control Ansible settings.


.. _the_configuration_file:

Configuration file
++++++++++++++++++

Certain settings in Ansible are adjustable via a configuration file (ansible.cfg).
The stock configuration should be sufficient for most users, but there may be reasons you would want to change them.

.. _getting_the_latest_configuration:

Getting the latest configuration
````````````````````````````````

If installing Ansible from a package manager, the latest ansible.cfg file should be present in /etc/ansible, possibly
as a ".rpmnew" file (or other) as appropriate in the case of updates.

If you installed Ansible from pip or from source, you may want to create this file in order to override
default settings in Ansible.

An `example file is available on Github <https://raw.github.com/ansible/ansible/devel/examples/ansible.cfg>`_.

For more details and a full listing of available configurations go to :doc:configuration. Starting with Ansible version 2.4, you can use the :doc:`ansible-config` command line utility to list your available options and inspect the current values.

For in depth details you check out :doc:`config`.


Environmental configuration
+++++++++++++++++++++++++++

Ansible also allows configuration of settings using environment variables.
If these environment variables are set, they will override any setting loaded from the configuration file.

You can get a full listing of available environment variables from :doc:`config`.

.. _command_line_configuration:

Command line options
++++++++++++++++++++

Not all configuration options are present in the command line, just the ones deemed most useful or common.
Settings in the command line will override those passed through the configuration file and the environment.

The full list of options available is in :doc:`ansible-playbook` and :doc:`ansible`.

.. seealso::

   :doc:`intro_dynamic_inventory`
       Pulling inventory from dynamic sources, such as cloud providers
   :doc:`intro_adhoc`
       Examples of basic commands
   :doc:`playbooks`
       Learning Ansible's configuration, deployment, and orchestration language.
   :doc:`config`
       Ansible's configuration file and environment settings in detail
   :doc:`command_line_tools`
       Ansible's command line tools documentation and detailed options
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

