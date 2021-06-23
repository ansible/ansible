.. _playbooks_async:

Asynchronous Actions and Polling
================================

By default tasks in playbooks block, meaning the connections stay open
until the task is done on each node.  This may not always be desirable, or you may
be running operations that take longer than the SSH timeout.

Time-limited background operations
----------------------------------

You can run long-running operations in the background and check their status later.
For example, to execute ``long_running_operation``
asynchronously in the background, with a timeout of 3600 seconds (``-B``),
and without polling (``-P``)::

    $ ansible all -B 3600 -P 0 -a "/usr/bin/long_running_operation --do-stuff"

If you want to check on the job status later, you can use the
``async_status`` module, passing it the job ID that was returned when you ran
the original job in the background::

    $ ansible web1.example.com -m async_status -a "jid=488359678239.2844"

To run for 30 minutes and poll for status every 60 seconds::

    $ ansible all -B 1800 -P 60 -a "/usr/bin/long_running_operation --do-stuff"

Poll mode is smart so all jobs will be started before polling will begin on any machine.
Be sure to use a high enough ``--forks`` value if you want to get all of your jobs started
very quickly. After the time limit (in seconds) runs out (``-B``), the process on
the remote nodes will be terminated.

Typically you'll only be backgrounding long-running
shell commands or software upgrades.  Backgrounding the copy module does not do a background file transfer. :ref:`Playbooks <working_with_playbooks>` also support polling, and have a simplified syntax for this.

To avoid blocking or timeout issues, you can use asynchronous mode to run all of your tasks at once and then poll until they are done.

The behavior of asynchronous mode depends on the value of `poll`.

Avoid connection timeouts: poll > 0
-----------------------------------

When ``poll`` is a positive value, the playbook will *still* block on the task until it either completes, fails or times out.

In this case, however, `async` explicitly sets the timeout you wish to apply to this task rather than being limited by the connection method timeout.

To launch a task asynchronously, specify its maximum runtime
and how frequently you would like to poll for status.  The default
poll value is set by the ``DEFAULT_POLL_INTERVAL`` setting if you do not specify a value for `poll`::

    ---

    - hosts: all
      remote_user: root

      tasks:

      - name: simulate long running op (15 sec), wait for up to 45 sec, poll every 5 sec
        command: /bin/sleep 15
        async: 45
        poll: 5

.. note::
   There is no default for the async time limit.  If you leave off the
   'async' keyword, the task runs synchronously, which is Ansible's
   default.

.. note::
  As of Ansible 2.3, async does not support check mode and will fail the
  task when run in check mode. See :ref:`check_mode_dry` on how to
  skip a task in check mode.


Concurrent tasks: poll = 0
--------------------------

When ``poll`` is 0, Ansible will start the task and immediately move on to the next one without waiting for a result.

From the point of view of sequencing this is asynchronous programming: tasks may now run concurrently.

The playbook run will end without checking back on async tasks.

The async tasks will run until they either complete, fail or timeout according to their `async` value.

If you need a synchronization point with a task, register it to obtain its job ID and use the :ref:`async_status <async_status_module>` module to observe it.

You may run a task asynchronously by specifying a poll value of 0::

    ---

    - hosts: all
      remote_user: root

      tasks:

      - name: simulate long running op, allow to run for 45 sec, fire and forget
        command: /bin/sleep 15
        async: 45
        poll: 0

.. note::
   You shouldn't attempt run a task asynchronously by specifying a poll value of 0 with operations that require
   exclusive locks (such as yum transactions) if you expect to run other
   commands later in the playbook against those same resources.

.. note::
   Using a higher value for ``--forks`` will result in kicking off asynchronous
   tasks even faster.  This also increases the efficiency of polling.

If you would like to perform a task asynchronously and check on it later you can perform a task similar to the
following::

      ---
      # Requires ansible 1.8+
      - name: 'YUM - async task'
        yum:
          name: docker-io
          state: present
        async: 1000
        poll: 0
        register: yum_sleeper

      - name: 'YUM - check on async task'
        async_status:
          jid: "{{ yum_sleeper.ansible_job_id }}"
        register: job_result
        until: job_result.finished
        retries: 30

.. note::
   If the value of ``async:`` is not high enough, this will cause the
   "check on it later" task to fail because the temporary status file that
   the ``async_status:`` is looking for will not have been written or no longer exist

If you would like to run multiple asynchronous tasks while limiting the amount
of tasks running concurrently, you can do it this way::

    #####################
    # main.yml
    #####################
    - name: Run items asynchronously in batch of two items
      vars:
        sleep_durations:
          - 1
          - 2
          - 3
          - 4
          - 5
        durations: "{{ item }}"
      include_tasks: execute_batch.yml
      loop: "{{ sleep_durations | batch(2) | list }}"

    #####################
    # execute_batch.yml
    #####################
    - name: Async sleeping for batched_items
      command: sleep {{ async_item }}
      async: 45
      poll: 0
      loop: "{{ durations }}"
      loop_control:
        loop_var: "async_item"
      register: async_results

    - name: Check sync status
      async_status:
        jid: "{{ async_result_item.ansible_job_id }}"
      loop: "{{ async_results.results }}"
      loop_control:
        loop_var: "async_result_item"
      register: async_poll_results
      until: async_poll_results.finished
      retries: 30

.. seealso::

   :ref:`playbooks_intro`
       An introduction to playbooks
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.libera.chat <https://libera.chat/>`_
       #ansible IRC chat channel
