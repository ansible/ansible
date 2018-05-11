.. _playbooks_async:

Asynchronous Actions and Polling
================================

By default tasks in playbooks block, meaning the connections stay open
until the task is done on each node.  This may not always be desirable, or you may
be running operations that take longer than the SSH timeout.

To avoid blocking or timeout issues, you can use asynchronous mode to run all of your tasks at once and then poll until they are done.

To launch a task asynchronously, specify its maximum runtime
and how frequently you would like to poll for status.  The default
poll value is 10 seconds if you do not specify a value for `poll`::

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

Alternatively, if you do not need to wait on the task to complete, you may
run the task asynchronously by specifying a poll value of 0::

    ---

    - hosts: all
      remote_user: root

      tasks:

      - name: simulate long running op, allow to run for 45 sec, fire and forget
        command: /bin/sleep 15
        async: 45
        poll: 0

.. note::
   You shouldn't attempt run a task asynchronously by specifying a poll value of 0:: to with operations that require
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
          state: installed
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
      loop:
        - "{{ sleep_durations | batch(2) | list }}"

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

   :doc:`playbooks`
       An introduction to playbooks
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

