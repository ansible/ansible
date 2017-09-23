Shell Plugins
-------------

Shell plugins work transparently to ensure that the basic commands Ansible runs are properly formated to work with the target machine.

.. _enabling_shell:

Enabling Shell Plugins
++++++++++++++++++++++

You can add a custom shell plugins by either dropping it into a ``shell_plugins`` directory adjacent to your play or inside a role
or by putting it in one of the shell plugin directory sources configured in :doc:`ansible.cfg <../config>`.

.. warning:: You should not alter the configuration for these plugins unless you have a restricted or exotic setup
             in which the default ``/bin/sh`` is not a POSIX compatible shell or not availble for execution.

.. _using_shell:

Using Shell Plugins
+++++++++++++++++++

You probably never need to do this, but aside from the defaul configuration settings in :doc:`../config`,
you can use a 'connection variable' :ref:`ansible_shell_type` to select the plugin to use,
you will also want to update the :ref:`ansible_executable` to match.

.. seealso::

   :doc:`../playbooks`
       An introduction to playbooks
   :doc:`inventory`
       Ansible inventory plugins
   :doc:`callback`
       Ansible callback plugins
   :doc:`../playbooks_filters`
       Jinja2 filter plugins
   :doc:`../playbooks_tests`
       Jinja2 test plugins
   :doc:`../playbooks_lookups`
       Jinja2 lookup plugins
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
