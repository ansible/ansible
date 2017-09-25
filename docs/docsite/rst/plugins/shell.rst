Shell Plugins
-------------

Shell plugins work transparently to ensure that the basic commands Ansible runs are properly formated to work with the target machine.

Enabling Shell Plugins
++++++++++++++++++++++

.. warning:: These plugins should not be reconfigured unless you have a restricted or exotic setup
             in which the default ``/bin/sh`` is not a POSIX compatible shell or not availble for execution. 

In addition to modifying the default configuration settings in :doc:`../config`, you can use a 'connection variable' :ref:`ansible_shell_type` to select a shell plugin, and update the :ref:`ansible_executable` to match.

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
