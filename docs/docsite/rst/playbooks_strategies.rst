Strategies
===========

In 2.0 we added a new way to control play execution, ``strategy``, by default plays will
still run as they used to, with what we call the ``linear`` strategy. All hosts will run each
task before any host starts the next task, using the number of forks (default 5) to parallelize.

The ``serial`` directive can 'batch' this behaviour to a subset of the hosts, which then run to
completion of the play before the next 'batch' starts.

A second ``strategy`` ships with ansible ``free``, which allows each host to run until the end of
the play as fast as it can.::

    - hosts: all
      strategy: free
      tasks:
      ...


.. _strategy_plugins:

Strategy Plugins
`````````````````

The strategies are implemented via a new type of plugin, this means that in the future new
execution types can be added, either locally by users or to Ansible itself by
a code contribution.

One example is ``debug`` strategy. See :doc:`playbooks_debugger` for details.

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_reuse_roles`
       Playbook organization by roles
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

