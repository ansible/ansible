Blocks
======

In 2.0 we added a block feature to allow for logical grouping of tasks and even
in play error handling. Most of what you can apply to a single task can be applied
at the block level, which also makes it much easier to set data or directives common
to the tasks. This does not mean the directive affects the block itself, but is inherited
by the tasks enclosed by a block. i.e. a `when` will be applied to the tasks, not the block itself.


.. code-block:: YAML
 :emphasize-lines: 3
 :caption: Block example

    tasks:
      - name: Install Apache
        block:
          - yum: name={{ item }} state=installed
            with_items:
              - httpd
              - memcached
          - template: src=templates/src.j2 dest=/etc/foo.conf
          - service: name=bar state=started enabled=True
        when: ansible_distribution == 'CentOS'
        become: true
        become_user: root


In the example above, each of the 3 tasks will be executed after appending the `when` condition from the block
and evaluating it in the task's context. Also they inherit the privilege escalation directives enabling "become to root"
for all the enclosed tasks.

. versionadded:: 2.3

The `name:` keyword for `blocks:` was added in Ansible 2.3.

.. _block_error_handling:

Error Handling
``````````````

Blocks also introduce the ability to handle errors in a way similar to exceptions in most programming languages.

.. code-block:: YAML
 :emphasize-lines: 3,7,11
 :caption: Block error handling example

   tasks:
    - name: Attempt and gracefull roll back demo
      block:
        - debug: msg='I execute normally'
        - command: /bin/false
        - debug: msg='I never execute, due to the above task failing'
      rescue:
        - debug: msg='I caught an error'
        - command: /bin/false
        - debug: msg='I also never execute :-('
      always:
        - debug: msg="this always executes"


The tasks in the ``block`` would execute normally, if there is any error the ``rescue`` section would get executed
with whatever you need to do to recover from the previous error. The ``always`` section runs no matter what previous
error did or did not occur in the ``block`` and ``rescue`` sections.


Another example is how to run handlers after an error occurred :

.. code-block:: YAML
 :emphasize-lines: 5,9
 :caption: Block run handlers in error handling

  tasks:
    - name: Attempt and gracefull roll back demo
      block:
        - debug: msg='I execute normally'
          notify: run me even after an error
        - command: /bin/false
      rescue:
        - name: make sure all handlers run
          meta: flush_handlers
   handlers:
     - name: run me even after an error
       debug: msg='this handler runs even on error'

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_reuse_roles`
       Playbook organization by roles
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel



