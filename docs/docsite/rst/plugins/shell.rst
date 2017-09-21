Shell Plugins
-------------

These plugins work behind the scenes making sure the basic commands Ansible runs in order to be able to execute a task's action are
properly formated to work with the target machine.
You normally don't have to wory about these plugins at all unless you have a restricted or exotic setup in which the default ``/bin/sh`` is
not a POSIX compatible shell or not availble for execution..

Enabling Shell Plugins
++++++++++++++++++++++

You probably never need to do this, but aside from the defaul configuration settings in :doc:`../config`, you can use a 'connection variable'
:ref:`ansible_shell_type` to select the plugin to use, you will also want to update the :ref:`ansible_executable` to match.

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
