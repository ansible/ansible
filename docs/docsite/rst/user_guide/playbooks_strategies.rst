.. _playbooks_strategies:

Controlling playbook execution: strategies and more
===================================================

By default, Ansible runs each task on all hosts affected by a play before starting the next task on any host, using 5 forks. If you want to change this default behavior, you can use a different strategy plugin, change the number of forks, or apply one of several play-level keywords like ``serial``.

.. contents::
   :local:

Selecting a strategy
--------------------
The default behavior described above is the :ref:`linear strategy<linear_strategy>`. Ansible offers other strategies, including the :ref:`debug strategy<debug_strategy>` (see also  :ref:`playbook_debugger`) and the :ref:`free strategy<free_strategy>`, which allows
each host to run until the end of the play as fast as it can::

    - hosts: all
      strategy: free
      tasks:
      ...

You can select a different strategy for each play as shown above, or set your preferred strategy globally in ``ansible.cfg``, under the ``defaults`` stanza::

    [defaults]
    strategy = free

All strategies are implemented as :ref:`strategy plugins<strategy_plugins>`. Please review the documentation for each strategy plugin for details on how it works.

Setting the number of forks
---------------------------
If you have the processing power available and want to use more forks, you can set the number in ``ansible.cfg``::

    [defaults]
    forks = 30

or pass it on the command line: `ansible-playbook -f 30 my_playbook.yml`.

Using keywords to control execution
-----------------------------------
Several play-level :ref:`keyword<playbook_keywords>` also affect play execution. The most common one is ``serial``, which sets a number, a percentage, or a list of numbers of hosts you want to manage at a time. Setting ``serial`` with any strategy directs Ansible to 'batch' the hosts, completing the play on the specified number or percentage of hosts before starting the next 'batch'. This is especially useful for :ref:`rolling updates<rolling_update_batch_size>`.

The second keyword to affect execution is ``throttle``, which can also be used at the block and task level. This keyword limits the number of workers up to the maximum set via the forks setting or ``serial``. This can be useful in restricting tasks that may be CPU-intensive or interact with a rate-limiting API::

    tasks:
    - command: /path/to/cpu_intensive_command
      throttle: 1

Other keywords that affect play execution include ``ignore_errors``, ``ignore_unreachable``, and ``any_errors_fatal``. Please note that these keywords are not strategies. They are play-level directives or options.

.. seealso::

   :ref:`about_playbooks`
       An introduction to playbooks
   :ref:`playbooks_reuse_roles`
       Playbook organization by roles
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
