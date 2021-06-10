:orphan:

Ansible basic structures
========================
========================

To use Ansible you might want to pickup some basic terminology, though you find most terms in the :ref:`glossary`, here we have a quick rundown of the basics.

Basic concepts
==============

 * Playbook: a list of plays (sometimes also used to refer to the file that contains the plays) :ref:`playbooks_intro`
 * Play: ties a list of hosts to a list of tasks
 * Task: an action to execute on a host

A simple playbook with 1 play and 2 tasks, written in YAML:

.. code-block:: YAML

    - name: Sample playbook
      hosts: all
      vars:
        a_var: I am a variable value
      tasks:
        - name: I am a task that executes a command
          command: echo {{ a _var }}
          register: result

        - name: print result of command to screen
          debug:
            var: result.stdout

This is a YAML document, if you need to understand the structure above you might want to check out :ref:`yaml_syntax` first.

Keywords
--------
These are reserved words that help define the objects in an ansible playbook (plays, tasks, and the rest), above ``name``, ``register`` and ``hosts`` are 'keywords'.
They can be considered the 'Ansible Language'.  For a list of keywords and where you may place them you can consult :ref:`<playbook_keywords>`

On the command line, you can use ``ansbile-doc -t keywords -l`` to list all available and ``ansible-dco -t keywords <keyword>`` to get specific documentation.

Options
-------
These are plugin specific specific options, Ansible uses many plugin types, the most common is a 'module' (which defines a task's actions, see more below).
In the above example the last line ``var`` is an option of the ``debug`` action, indentation is normally a clue.

The options available are referenced in each plugin's specific documentation, for example you can check modules here :ref:`all_modules`,

On the command line you can also use ``ansible-doc -t modules -l`` to list all those avialable to you and ``ansible-doc -t modules <action name>`` to get the specific options.
Other plugins work the same way, just changing the plugin type (``-t``). Valid values are visible using ``--help``.



Tasks
=====

Tasks are the most common and used item in Ansible. They are the basis of everything else and they define the 'actions' to take against our targets. A task only requires an ``action``. This normally corresponds to an existing module and/or action plugin.

.. code-block:: YAML

    - debug: msg=simple task

A task is defined by the single action. There may only be one action per task. The ``name`` keyword within a task is optional, but it is used during the display of Ansible output.

.. code-block:: YAML

    - name: this is a simple task
      debug: msg=simple task

    - name: this is not a valid task because it has 2 actions
      debug: msg=simple task
      copy: src=/etc/localfile dest=/tmp/remotefile

As you may have noticed, tasks are always prefixed by a ``-``. This is because they are always an 'item of a list'.
Tasks may only exist inside 'task lists'. These task lists must reside inside a play, directly or indirectly, via a role, block, include or import.

There are two ways to specify the options of an action: 'key-value pairs' (``key=value``) and pure yaml (``key: value``)

.. code-block:: YAML

    - name: this is a YAML formatted task to copy a file from the controller to the target host
      copy:
        src: /etc/localfile
        dest: /tmp/remotefile

    - debug: msg='this is a key-value pair task'

Indentation is important in a task since it is used to separate the task keywords from the module/action options:

.. code-block:: YAML

    - name: this is the name keyword
      debug:
        msg: 'this is the msg option of the debug action'
      when: 'this is the conditional keyword for tasks' != 'so it must always align to the task itself'


Plays
=====

Plays are a simple mapping of hosts to tasks. Plays bind the actions we define to the targets we desire to apply them to.

.. code-block:: YAML

  - hosts: all

This is the simplest play. It just targets all hosts in inventory and (by default) runs M(gather_facts) on them.


There are many ways a play can contain tasks. The simplest one is the ``tasks`` keyword.

.. code-block:: YAML

    - hosts: all
      tasks:
        - name: this is a simple task
          debug: msg=simple task


This keyword begins the definition of a 'list of tasks'. Other ways a play can contain tasks is via the ``pre_tasks``, ``post_tasks`` and ``handlers`` keywords.

Plays may ONLY appear inside a playbook. You cannot put a play inside another play nor any other object. See playbooks above.



Playbooks
=========

The definition is simple, playbooks are a 'list of plays', this is normally used to refer to a file with plays, but can also mean an Ansible execution with multiple plays from one or more files. For now we are going to assume the former. A simple playbook as an example:

.. code-block:: YAML

    - hosts: all

This just contains one play, that targtes all hosts, but you can also have more than play (why it is a 'list of plays').

.. code-block:: YAML

    - name: first play
      hosts: some
      tasks:
        ...

    - name: second play
      hosts: others
      roles:
        ...

playbooks can ONLY have plays, you cannot put a task in a playbook, only inside a play.


Blocks, Roles and other advanced things
---------------------------------------

Once you get more familiar with Ansible, there are other parts of the playbook you should look into:

  * Blocks: A construct to group a list of tasks, set common keywords and handle errors :ref:`playbooks_blocks` and :ref:`playbooks_error_handling`
  * Roles: A way to bundle Tasks, variables and other things for reuse :ref:`playbooks_reuse_roles`
  * Handlers are a special kind of task that only executes conditioned on another linked task being in 'changed' state :ref:`_handlers`

There are also imports and includes :ref:`playbooks_reuse` as ways to reuse Ansible content, though similar the behave differently.
Imports are 'static', don't really behave like normal tasks and used moslty for inheritance.
Includes are 'dynamic' and behave much more like a normal task, but also require more resources.


Full example
============

The following is the contents of a ``site.yml`` playbook.

.. code-block:: YAML
   :caption: playbook
   :emphasize-lines: 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23

   - name: setup webservers
       hosts: webservers
       tasks:
          - yum: name=apache state=present
            notify: apache_started

       handlers:
         - name: apache_started
           service: name=apache state=started

     - hosts: apiservers
       pre_tasks:
           - name: Remove repository (and clean up left-over metadata)
             yum_repository:
               name: epel
               state: present
       roles:
         - django
         - postgresql_client
       post_tasks:
         - include_role:
               name: internal_firewall

     - import_playbook: dbservers.yml


Now we just highlight the plays.

.. code-block:: YAML
   :caption: plays
   :emphasize-lines: 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21

   - name: setup webservers
     hosts: webservers
     tasks:
        - yum: name=apache state=present
          notify: apache_started

     handlers:
       - name: apache_started
         service: name=apache state=started

   - hosts: apiservers
     pre_tasks:
         - name: Remove repository (and clean up left-over metadata)
           yum_repository:
             name: epel
             state: present
     roles:
       - django
       - postgresql_client
     post_tasks:
       - include_role:
             name: internal_firewall

   - import_playbook: dbservers.yml


Now just the tasks.

.. code-block:: YAML
   :caption: tasks
   :emphasize-lines: 4,5,8,9,13,14,15,16,21,22

   - name: setup webservers
     hosts: webservers
     tasks:
        - yum: name=apache state=present
          notify: apache_started

     handlers:
       - name: apache_started
         service: name=apache state=started

   - hosts: apiservers
     pre_tasks:
         - name: Remove repository (and clean up left-over metadata)
           yum_repository:
             name: epel
             state: present
     roles:
       - django
       - postgresql_client
     post_tasks:
       - include_role:
             name: internal_firewall

   - import_playbook: dbservers.yml


There is a lot more to Ansible, but this should be the minimal you need to start writing your own playbooks, plays and tasks.

.. seealso::

   :ref:`working_with_playbooks`
       Review the basic Playbook language features
   :ref:`playbooks_variables`
       All about variables in playbooks
   :ref:`playbooks_conditionals`
       Conditionals in playbooks
   :ref:`playbooks_loops`
       Loops in playbooks
   `GitHub Ansible examples <https://github.com/ansible/ansible-examples>`_
       Complete playbook files from the GitHub project source
   `Mailing List <https://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
