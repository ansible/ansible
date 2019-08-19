.. _playbooks_templating:

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

.. _templating_now:

Get the current time
````````````````````

.. versionadded:: 2.8

The ``now()`` Jinja2 function, allows you to retrieve python datetime object or a string representation for the current time.

The ``now()`` function supports 2 arguments:

utc
  Specify ``True`` to get the current time in UTC. Defaults to ``False``

fmt
  Accepts a `strftime <https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior>`_ string that will be used
  to return a formatted date time string


.. seealso::

   :ref:`playbooks_intro`
       An introduction to playbooks
   :ref:`playbooks_conditionals`
       Conditional statements in playbooks
   :ref:`playbooks_loops`
       Looping in playbooks
   :ref:`playbooks_reuse_roles`
       Playbook organization by roles
   :ref:`playbooks_best_practices`
       Best practices in playbooks
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
