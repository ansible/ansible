.. _playbooks_blocks:

Blocks
======

Blocks allow for logical grouping of tasks and in play error handling. Most of what you can apply to a single task (with the exception of loops) can be applied at the block level, which also makes it much easier to set data or directives common to the tasks. This does not mean the directive affects the block itself, but is inherited by the tasks enclosed by a block. i.e. a `when` will be applied to the tasks, not the block itself.


.. code-block:: YAML
 :emphasize-lines: 3
 :caption: Block example with named tasks inside the block

  tasks:
    - name: Install, configure, and start Apache
      block:
        - name: install httpd and memcached
          yum:
            name:
            - httpd
            - memcached
            state: present

        - name: apply the foo config template
          template:
            src: templates/src.j2
            dest: /etc/foo.conf
        - name: start service bar and enable it
          service:
            name: bar
            state: started
            enabled: True
      when: ansible_facts['distribution'] == 'CentOS'
      become: true
      become_user: root
      ignore_errors: yes

In the example above, each of the 3 tasks will be executed after appending the `when` condition from the block
and evaluating it in the task's context. Also they inherit the privilege escalation directives enabling "become to root"
for all the enclosed tasks. Finally, ``ignore_errors: yes`` will continue executing the playbook even if some of the tasks fail.

Names for tasks within blocks have been available since Ansible 2.3. We recommend using names in all tasks, within blocks or elsewhere, for better visibility into the tasks being executed when you run the playbook.

.. _block_error_handling:

Blocks error handling
`````````````````````

Blocks also introduce the ability to handle errors in a way similar to exceptions in most programming languages.
Blocks only deal with 'failed' status of a task. A bad task definition or an unreachable host are not 'rescuable' errors.

.. _block_rescue:
.. code-block:: YAML
 :emphasize-lines: 3,10
 :caption: Block error handling example

  tasks:
  - name: Handle the error
    block:
      - debug:
          msg: 'I execute normally'
      - name: i force a failure
        command: /bin/false
      - debug:
          msg: 'I never execute, due to the above task failing, :-('
    rescue:
      - debug:
          msg: 'I caught an error, can do stuff here to fix it, :-)'

This will 'revert' the failed status of the task for the run and the play will continue as if it had succeeded.

There is also an ``always`` section, that will run no matter what the task status is.

.. _block_always:
.. code-block:: YAML
 :emphasize-lines: 2,9
 :caption: Block with always section

  - name: Always do X
    block:
      - debug:
          msg: 'I execute normally'
      - name: i force a failure
        command: /bin/false
      - debug:
          msg: 'I never execute :-('
    always:
      - debug:
          msg: "This always executes, :-)"

They can be added all together to do complex error handling.

.. code-block:: YAML
 :emphasize-lines: 2,9,16
 :caption: Block with all sections

 - name: Attempt and graceful roll back demo
   block:
     - debug:
         msg: 'I execute normally'
     - name: i force a failure
       command: /bin/false
     - debug:
         msg: 'I never execute, due to the above task failing, :-('
   rescue:
     - debug:
         msg: 'I caught an error'
     - name: i force a failure in middle of recovery! >:-)
       command: /bin/false
     - debug:
         msg: 'I also never execute :-('
   always:
     - debug:
         msg: "This always executes"


The tasks in the ``block`` would execute normally, if there is any error the ``rescue`` section would get executed
with whatever you need to do to recover from the previous error.
The ``always`` section runs no matter what previous error did or did not occur in the ``block`` and ``rescue`` sections.
It should be noted that the play continues if a ``rescue`` section completes successfully as it 'erases' the error status (but not the reporting),
this means it won't trigger ``max_fail_percentage`` nor ``any_errors_fatal`` configurations but will appear in the playbook statistics.

Another example is how to run handlers after an error occurred :

.. code-block:: YAML
 :emphasize-lines: 6,10
 :caption: Block run handlers in error handling


  tasks:
    - name: Attempt and graceful roll back demo
      block:
        - debug:
            msg: 'I execute normally'
          changed_when: yes
          notify: run me even after an error
        - command: /bin/false
      rescue:
        - name: make sure all handlers run
          meta: flush_handlers
  handlers:
     - name: run me even after an error
       debug:
         msg: 'This handler runs even on error'


.. versionadded:: 2.1

Ansible also provides a couple of variables for tasks in the ``rescue`` portion of a block:

ansible_failed_task
    The task that returned 'failed' and triggered the rescue. For example, to get the name use ``ansible_failed_task.name``.

ansible_failed_result
    The captured return result of the failed task that triggered the rescue. This would equate to having used this var in the ``register`` keyword.

.. seealso::

   :ref:`playbooks_intro`
       An introduction to playbooks
   :ref:`playbooks_reuse_roles`
       Playbook organization by roles
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.libera.chat <https://libera.chat/>`_
       #ansible IRC chat channel
