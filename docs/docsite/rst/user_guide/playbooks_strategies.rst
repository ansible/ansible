.. _playbooks_strategies:

Strategies
===========

Strategies control play execution. By default, plays run with the :ref:`linear strategy<linear_strategy>`, in which all hosts will run each task before any host starts the next task, using the number of forks (default 5) to parallelize.

Ansible offers other strategies, including the :ref:`debug strategy<debug_strategy>` (see also  :ref:`playbook_debugger`) and the :ref:`free strategy<free_strategy>`, which allows
each host to run until the end of the play as fast as it can::

    - hosts: all
      strategy: free
      tasks:
      ...

You can select a different strategy for each play, or set your preferred strategy globally in ``ansible.cfg``, under the ``defaults`` stanza::

    [defaults]
    strategy = free

All strategies are implemented as :ref:`strategy plugins<strategy_plugins>`. Please review the documentation for each strategy plugin for details on how it works.

You can also use the play-level :ref:`keyword<playbooks_keywords>` ``serial``
to set the number or percentage of hosts you want to manage at a time with any
strategy. Ansible will then 'batch' the hosts, completing the play on the specified number or percentage of hosts before starting the next 'batch'.
This is especially useful for :ref:`rolling updates<rolling_update_batch_size>`. Please note that ``serial`` is not a strategy, but a play-level directive/option.

.. seealso::

   :ref:`about_playbooks`
       An introduction to playbooks
   :ref:`playbooks_reuse_roles`
       Playbook organization by roles
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
