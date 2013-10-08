Loops
=====

.. contents::
   :depth: 2

Often you'll want to do many things in one task, such as create a lot of users, install a lot of packages, or
repeat a polling step until a certain result is reached.

This chapter is all about how to use loops in playbooks.

.. _standard_loops:

Standard Loops
``````````````

To save some typing, repeated tasks can be written in short-hand like so::

    - name: add several users
      user: name={{ item }} state=present groups=wheel
      with_items:
         - testuser1
         - testuser2

If you have defined a YAML list in a variables file, or the 'vars' section, you can also do::

    with_items: somelist

The above would be the equivalent of::

    - name: add user testuser1
      user: name=testuser1 state=present groups=wheel
    - name: add user testuser2
      user: name=testuser2 state=present groups=wheel

The yum and apt modules use with_items to execute fewer package manager transactions.

Note that the types of items you iterate over with 'with_items' do not have to be simple lists of strings.
If you have a list of hashes, you can reference subkeys using things like::

    - name: add several users
      user: name={{ item.name }} state=present groups={{ item.groups }}
      with_items:
        - { name: 'testuser1', groups: 'wheel' }
        - { name: 'testuser2', groups: 'root' }

.. _nested_loops:

Nested Loops
````````````

Loops can be nested as well::

    - name: give users access to multiple databases
      mysql_user: name={{ item[0] }} priv={{ item[1] }}.*:ALL append_privs=yes password=foo
      with_nested:
        - [ 'alice', 'bob', 'eve' ]
        - [ 'clientdb', 'employeedb', 'providerdb' ]

As with the case of 'with_items' above, you can use previously defined variables. Just specify the variable's name without templating it with '{{ }}'::

    - name: here, 'users' contains the above list of employees
      mysql_user: name={{ item[0] }} priv={{ item[1] }}.*:ALL append_privs=yes password=foo
      with_nested:
        - users
        - [ 'clientdb', 'employeedb', 'providerdb' ]

.. _looping_over_fileglobs:

Looping over Fileglobs
``````````````````````

``with_fileglob`` matches all files in a single directory, non-recursively, that match a pattern.  It can
be used like this::

    ---
    - hosts: all

      tasks:

        # first ensure our target directory exists
        - file: dest=/etc/fooapp state=directory

        # copy each file over that matches the given pattern
        - copy: src={{ item }} dest=/etc/fooapp/ owner=root mode=600
          with_fileglob:
            - /playbooks/files/fooapp/*

Looping over Parallel Sets of Data
``````````````````````````````````

.. note:: This is an uncommon thing to want to do, but we're documenting it for completeness.  You won't be reaching for this one often.

Suppose you have the following variable data was loaded in via somewhere::

    ---
    alpha: [ 'a', 'b', 'c', 'd' ]
    numbers:  [ 1, 2, 3, 4 ]

And you want the set of '(a, 1)' and '(b, 2)' and so on.   Use 'with_together' to get this::

    tasks:
        - debug: msg="{{ item.0 }} and {{ item.1 }}"
          with_together:
            - alpha
            - numbers

Looping over Subelements
````````````````````````

Suppose you want to do something like loop over a list of users, creating them, and allowing them to login by a certain set of
SSH keys. 

How might that be accomplished?  Let's assume you had the following defined and loaded in via "vars_files" or maybe a "group_vars/all" file::

    ---
    users:
      - name: alice
        authorized: 
          - /tmp/alice/onekey.pub
          - /tmp/alice/twokey.pub
      - name: bob
        authorized:
          - /tmp/bob/id_rsa.pub

It might happen like so::

    - user: name={{ item.name }} state=present generate_ssh_key=yes
      with_items: users

    - authorized_key: user={{ item.0.name }} key={{ lookup('file', item.1) }}
      with_subelements:
         - users
         - authorized

Subelements walks a list of hashes (aka dictionaries) and then traverses a list with a given key inside of those
records.

The authorized_key pattern is exactly where it comes up most.

.. _looping_over_integer_sequences:

Looping over Integer Sequences
``````````````````````````````

``with_sequence`` generates a sequence of items in ascending numerical order. You
can specify a start, end, and an optional step value.

Arguments should be specified in key=value pairs.  If supplied, the 'format' is a printf style string.

Numerical values can be specified in decimal, hexadecimal (0x3f8) or octal (0600).
Negative numbers are not supported.  This works as follows::

    ---
    - hosts: all

      tasks:

        # create groups
        - group: name=evens state=present
        - group: name=odds state=present

        # create some test users
        - user: name={{ item }} state=present groups=evens
          with_sequence: start=0 end=32 format=testuser%02x

        # create a series of directories with even numbers for some reason
        - file: dest=/var/stuff/{{ item }} state=directory
          with_sequence: start=4 end=16 stride=2

        # a simpler way to use the sequence plugin
        # create 4 groups
        - group: name=group{{ item }} state=present
          with_sequence: count=4

.. _random_choice:

Random Choices
``````````````

The 'random_choice' feature can be used to pick something at random.  While it's not a load balancer, it can
somewhat be used as a poor man's loadbalancer in a MacGyver like situation::

    - debug: msg={{ item }}
      with_random_choice:
         - "go through the door"
         - "drink from the goblet"
         - "press the red button"
         - "do nothing"

One of the provided strings will be selected at random.  

At a more basic level, they can be used to add chaos and excitement to otherwise predictable automation environments.

.. _do_until_loops:

Do-Until Loops
``````````````

Sometimes you would want to retry a task until a certain condition is met.  Here's an example::
   
    - action: shell /usr/bin/foo
      register: result
      until: result.stdout.find("all systems go") != -1
      retries: 5
      delay: 10

The above example run the shell module recursively till the module's result has "all systems go" in it's stdout or the task has 
been retried for 5 times with a delay of 10 seconds. The default value for "retries" is 3 and "delay" is 5.

The task returns the results returned by the last task run. The results of individual retries can be viewed by -vv option.
The registered variable will also have a new key "attempts" which will have the number of the retries for the task.

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


