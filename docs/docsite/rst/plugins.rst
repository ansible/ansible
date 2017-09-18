Plugins
=======

Ansible uses a plugin architecture to enable a rich, flexible and expandible feature set.
They are pieces of code that augment Ansible's core functionality.
Ansible ships with a number of handy plugins, and you can easily write your own.

There are many types of plugins, these are the most relevant ones:

- *:doc:`Action plugins/action`* plugins are front ends to modules and can execute actions on the controller before calling the modules themselves. Normally transparent to users.
- *:doc:`Cache plugins/cache`* plugins are used to keep a cache of 'facts' to avoid costly fact-gathering or inventory operations.
- *:doc:`Callback plugins/callback`* plugins enable you to hook into Ansible events for display, notification or logging purposes.
- *:doc:`Connection plugins/connection`* plugins define how to communicate with inventory hosts.
- *:doc:`Filters playbooks_filters`* plugins allow you to manipulate data inside Ansible plays and/or templates. This is a Jinja2 feature; Ansible ships extra filter plugins.
- *:doc:`Inventory plugins/inventory`* plugins allow you create and change the Inventory of hosts that Ansible uses as targets for it's tasks.
- *:doc:`Lookup playbooks_lookup`* plugins are used to pull data from an external source. They are an Ansible custom function injected into Jinja2, making them availabe for templates.
- *:doc:`Modules modules`* most people are familiar with, they execute the actions described by tasks, they work in conjunction with action plugins.
- *:doc:`Strategy plugins/strategy`* plugins control the flow of a play and execution logic.
- *:doc:`Shell plugins/shell`* plugins deal with low-level commands and formatting for the different shells Ansible can encounter on remote hosts.
- *:doc:`Test playbooks_test`* plugins allow you to validate data inside Ansible plays and/or templates. This is a Jinja2 feature; Ansible ships extra ones.
- *:doc:`Vars plugins/vars`* plugins inject additional variable data into Ansible runs that did not come from an inventory source, playbook, or the command line.

Most of the time you are using them without having to know about them, but when you want to change certain behaviours you need to know how to enable,
activate or trigger each type.

You can get a complete list from :doc:`list_of_all_plugins`.

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`config`
       Ansible configuration documentation and settings
   :doc:`command_line_tools`
       Ansible tools, description and options
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
