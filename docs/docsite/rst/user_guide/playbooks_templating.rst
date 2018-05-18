Templating (Jinja2)
===================

As already referenced in the variables section, Ansible uses Jinja2 templating to enable dynamic expressions and access to variables.
Ansible greatly expands the number of filters and tests available, as well as adding a new plugin type: lookups.

Please note that all templating happens on the Ansible controller before the task is sent and executed on the target machine. This is done to minimize the requirements on the target (jinja2 is only required on the controller) and to be able to pass the minimal information needed for the task, so the target machine does not need a copy of all the data that the controller has access to.

.. contents:: Topics

.. toctree::
   :maxdepth: 2

   playbooks_filters
   playbooks_tests
   playbooks_lookups
   playbooks_python_version


.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_conditionals`
       Conditional statements in playbooks
   :doc:`playbooks_loops`
       Looping in playbooks
   :doc:`playbooks_reuse_roles`
       Playbook organization by roles
   :doc:`playbooks_best_practices`
       Best practices in playbooks
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


