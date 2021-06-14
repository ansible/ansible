.. _playbooks_templating:

*******************
Templating (Jinja2)
*******************

Ansible uses Jinja2 templating to enable dynamic expressions and access to variables. Ansible includes a lot of specialized filters and tests for templating. You can use all the :ref:`standard filters and tests <jinja2:builtin-filters>` included in Jinja2 as well. Ansible also offers a new plugin type: :ref:`lookup_plugins`.

All templating happens on the Ansible controller **before** the task is sent and executed on the target machine. This approach minimizes the package requirements on the target (jinja2 is only required on the controller). It also limits the amount of data Ansible passes to the target machine. Ansible parses templates on the controller and passes only the information needed for each task to the target machine, instead of passing all the data on the controller and parsing it on the target.

.. contents::
   :local:

.. toctree::
   :maxdepth: 2

   playbooks_filters
   playbooks_tests
   playbooks_lookups
   playbooks_python_version

.. _templating_now:

Get the current time
====================

.. versionadded:: 2.8

The ``now()`` Jinja2 function retrieves a Python datetime object or a string representation for the current time.

The ``now()`` function supports 2 arguments:

utc
  Specify ``True`` to get the current time in UTC. Defaults to ``False``.

fmt
  Accepts a `strftime <https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior>`_ string that returns a formatted date time string.


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
       Tips and tricks for playbooks
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.libera.chat <https://libera.chat/>`_
       #ansible IRC chat channel
