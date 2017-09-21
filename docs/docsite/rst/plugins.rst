Plugins
=======

Ansible uses a plugin architecture to enable a rich, flexible and expandible feature set.
They are pieces of code that augment Ansible's core functionality.
Ansible ships with a number of handy plugins, and you can easily write your own.

There are many types of plugins, these are the most relevant ones:

.. toctree:: :maxdepth: 1
    :glob:

    plugins/*
    playbooks_filters
    playbooks_tests

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
