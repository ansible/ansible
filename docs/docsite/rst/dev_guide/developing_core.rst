**********************************
Developing the Ansible Core Engine
**********************************

Although many of the pieces of the Ansible Core Engine are plugins that can be
swapped out via playbook directives or configuration, there are still pieces
of the Engine that are not modular.  The documents here give insight into how
those pieces work together.

.. toctree::
   :maxdepth: 1

   developing_program_flow_modules

.. seealso::

   :ref:`developing_api`
       Learn about the Python API for task execution
   :ref:`developing_plugins`
       Learn about developing plugins
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
   `irc.libera.chat <https://libera.chat>`_
       #ansible-devel IRC chat channel
