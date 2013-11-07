Tasks
=====

.. contents::
   :depth: 2

Playbook tasks can have a few different formats and can take many different keywords.

.. _task_formats:

Task Formats
++++++++++++++++++++++

Basic
``````````````

The first keyword in a task can be the module name::

   - debug: msg="hello world"

It can also be a name::

   - name: a task with a name
     debug: msg="hello world"

Args can be separated to newlines::

   - copy: src=/srv/myfiles/foo.conf 
           dest=/etc/foo.conf

Old style with args inline::

   - action: debug 'msg="hello world"'

Old style with a name defined::

    - action: debug 'msg="hello world"'
      name: a task with aname

Old style with args as a dictionary::

    - action: debug
      args:
        msg: "hello world"


Connection Types
````````````````

Setting the connection type to local::

   - debug: msg="hello world"
     connection: local

Setting the connection type to ssh::

   - debug: msg="hello world"
     connection: ssh

Old style with a local connection::

   - local_action: debug 'msg="hello world"'


.. _task_keywords:

Task Keywords
++++++++++++++++++++++

Valid keywords for tasks in playbooks.

action
``````````````

always_run
``````````````
:doc:`playbooks_checkmode`

any_errors_fatal
````````````````
:doc:`playbooks_error_handling`

args
``````````````

async
``````````````
:doc:`playbooks_async`


changed_when
``````````````
:doc:`playbooks_error_handling`

connection
``````````````
:doc:`playbooks_delegation`

delay
``````````````

delegate_to
``````````````
:doc:`playbooks_delegation`

environment
``````````````

failed_when
``````````````
:doc:`playbooks_error_handling`

first_available_file
````````````````````

ignore_errors
``````````````
:doc:`playbooks_error_handling`

local_action
``````````````
:doc:`playbooks_delegation`

name
``````````````

notify
``````````````
:doc:`playbooks`

only_if
``````````````

poll
``````````````
:doc:`playbooks_async`

register
``````````````
:doc:`playbooks_variables`
:doc:`playbooks_loops`

remote_user
``````````````
:doc:`playbooks`

retries
``````````````
:doc:`playbooks_loops`

sudo
``````````````

sudo_user
``````````````

sudo_pass
``````````````

tags
``````````````
:doc:`playbooks_tags`

transport
``````````````
:doc:`playbooks_delegation`

until
``````````````
:doc:`playbooks_loops`

when
``````````````
:doc:`playbooks_conditionals`

with_dnstext
``````````````
:doc:`playbooks_loops`

with_env
``````````````
:doc:`playbooks_loops`

with_file
``````````````
:doc:`playbooks_loops`

with_fileglob
``````````````
:doc:`playbooks_loops`

with_first_found
````````````````
:doc:`playbooks_loops`

with_flattened
``````````````
:doc:`playbooks_loops`

with_indexed_items
``````````````````
:doc:`playbooks_loops`

with_inventory_hostnames
````````````````````````
:doc:`playbooks_loops`

with_items
``````````````
:doc:`playbooks_loops`

with_lines
``````````````
:doc:`playbooks_loops`

with_nested
``````````````
:doc:`playbooks_loops`

with_password
``````````````
:doc:`playbooks_loops`

with_pipe
``````````````
:doc:`playbooks_loops`

with_random_choice
``````````````````
:doc:`playbooks_loops`

with_redis_kv
``````````````
:doc:`playbooks_loops`

with_sequence
``````````````
:doc:`playbooks_loops`

with_subelements
````````````````
:doc:`playbooks_loops`

with_template
``````````````
:doc:`playbooks_loops`

with_together
``````````````
:doc:`playbooks_loops`

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_roles`
       Playbook organization by roles
   :doc:`playbooks_best_practices`
       Best practices in playbooks
   :doc:`playbooks_conditionals`
       Conditional statements in playbooks
   :doc:`playbooks_variables`
       All about variables
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


