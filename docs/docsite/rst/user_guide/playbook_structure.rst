:orphan:

Ansible basic structures introduction
=====================================
=====================================

Introcduction
=============

To use Ansible you might want to pickup some basic terminology, though you find most terms in the :ref:`glossary`, here we have a quick rundown of the basics.

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

To understand the structure above you might want to check out the YAML Basics


YAML Basics
===========
YAML is a data formatting language. It is 'space sensitive' and relies on indentation rather than having tags (for example ``<stuff> </endstuff>``) or other separators (``{``, ``}``, ``(``, ``)``, etc). It does have a 'short form' that looks a lot like JSON, but it is less strict about quoting. Most YAML parsers can read JSON directly.

The most basic types are simple. A string looks like a string, so does a number, but once you get into 'container' types, you run into issues. The most basic containers are lists (aka arrays, stacks, etc) and dictionaries (aka mappings, associative arrays, hashes, etc).


A ``-`` character identifies a 'list item'.

.. code-block:: YAML

    - one
    - two
    - three

Or in short form YAML.

.. code-block:: YAML

    [one, two, three]

A word with a colon (word:) identifies a mapping/dictionary

.. code-block:: YAML

    this: mapping
    has: two keys

Also in short form:

.. code-block:: YAML

    {this: mapping, has: 'two keys'}


They can intermix so you can have a list of dictionaries and lists in dictionaries as well as lists of lists and dictionaries within dictionaries …

.. code-block:: YAML

    this_list:
        - 1
        - 2
        - hasadict: with
          several: keys
          and: values
          with:
            - a
            - list
            - also


'---'
-----

What is the ``---`` we see on top of YAML files? This is a 'document separator'. It is an OPTIONAL indicator that a YAML document is starting and not needed for Ansible to function (though some linting programs will complain if it is missing). You may also see a related delimiter ``...``, which is also optional, that means 'end of document'.


For more details on YAML you can go here :ref:`yaml_syntax`.


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

As you may have noticed, tasks are always prefixed by a `-`. This is because they are always an 'item of a list'. Tasks may only exist inside 'task lists'. These task lists must reside inside a play, directly or indirectly, via a role, block, include or import.

There are two ways to specify the arguments of a task: 'key-value pairs' (e.g., `key=value`) and pure yaml (e.g., `key: value`)

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

For a list of keywords and the where you can place them see ...

Handlers
--------

Handlers are special tasks, not on how you define them, but on where they are located, they do not execute normally but on notification.For more information on handlers see here:


Plays
=====

Plays are a simple mapping of hosts to tasks, plays bind the actions we define to the targets we desire to apply them to.

.. code-block:: YAML

  - hosts: all

is the simplest play, it just targets all hosts in inventory and (by default) runs M(gather_facts) on them.


There are many ways a play can contain tasks, the simplest one is the ``tasks`` keyword.

.. code-block:: YAML

    - hosts: all
      tasks:
        - name: this is a simple task
          debug: msg=simple task


This keyword begins the definition of a 'list of tasks'. Other ways a play can contain tasks is via the ``pre_tasks``, ``post_tasks`` and ``handlers`` keywords.

Plays may ONLY appear inside a playbook. You cannot put a play inside another play nor any other object. See playbooks above.

Blocks, Roles and other things
------------------------------

Once you get more familiar with Ansible, there are other parts of the playbook you should look into:

  * Blocks: A construct to group a list of tasks, set common keywords  and handle errors :ref:`playbooks_blocks`
  * Roles: A way to bundle Tasks, variables and other things for reuse :ref:`playbooks_reuse_roles`

There are also imports and includes :ref:`playbooks_reuse` as ways to reuse Ansible content, though similar the behave differently.
Imports are 'static', don't really behave like normal tasks and used moslty for inheritance.
Includes are 'dynamic' and behave much more like a normal task, but also require more resources.


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

import_playbook
---------------
Now this might be a bit confusing due to the following being a valid playbook.

.. code-block:: YAML

   - hosts: all

   - import_playbook: play.yml

This looks like we are mixing plays and tasks, but that is not true, the M(import_playbook) is a special directive that allows referencing other playbook files and importing them into the current one, as such it is not considered a 'real task' and is allowed in playbooks. Note that you can have a list of plays imported by M(import_playbook), not just one play.


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
