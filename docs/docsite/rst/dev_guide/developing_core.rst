***************************
Developing ``ansible-core``
***************************

Although ``ansible-core`` (the code hosted in the `ansible/ansible repository <https://github.com/ansible/ansible>`_ on GitHub) includes a few plugins that can be swapped out via playbook directives or configuration, much of the code there is not modular.  The documents here give insight into how the parts of ``ansible-core`` work together.

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
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible-devel IRC chat channel
