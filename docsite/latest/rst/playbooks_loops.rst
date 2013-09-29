Loops
=====

All about how to use loops in playbooks.


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

Nested Loops
````````````

Loops can be nested as well::

    - name: give users access to multiple databases
      mysql_user: name={{ item[0] }} priv={{ item[1] }}.*:ALL password=foo
      with_nested:
        - [ 'alice', 'bob', 'eve' ]
        - [ 'clientdb', 'employeedb', 'providerdb' ]

As with the case of 'with_items' above, you can use previously defined variables. Just specify the variable's name without templating it with '{{ }}'::

    - name: here, 'users' contains the above list of employees
      mysql_user: name={{ item[0] }} priv={{ item[1] }}.*:ALL password=foo
      with_nested:
        - users
        - [ 'clientdb', 'employeedb', 'providerdb' ]

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

Documentation for this feature is coming soon.

Looping over Subelements
````````````````````````

Documentation for this feature is coming soon.


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

Do-Until Loops
``````````````

Sometimes you would want to retry a task until a certain condition is met.  Here's an example::
   
    - action: shell /usr/bin/foo
      register: result
      until: register.stdout.find("all systems go") != -1
      retries: 5
      delay: 10

The above example run the shell module recursively till the module's result has "all systems go" in it's stdout or the task has 
been retried for 5 times with a delay of 10 seconds. The default value for "retries" is 3 and "delay" is 5.

The task returns the results returned by the last task run. The results of individual retries can be viewed by -vv option.
The registered variable will also have a new key "attempts" which will have the number of the retries for the task.

The Do/Until feature does not take decision on whether to fail or pass the play when the maximum retries are completed, the user can 
can do that in the next task as follows::
   
   - action: shell /usr/bin/foo
     register: result
     until: register.stdout.find("all systems go") != -1
     retries: 5
     delay: 10
     failed_when: result.attempts == 5




