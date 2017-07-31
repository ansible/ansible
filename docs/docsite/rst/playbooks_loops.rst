Loops
=====

Often you'll want to do many things in one task, such as create a lot of users, install a lot of packages, or
repeat a polling step until a certain result is reached.

This chapter is all about how to use loops in playbooks.

.. contents:: Topics

.. _standard_loops:

Standard Loops
``````````````

To save some typing, repeated tasks can be written in short-hand like so::

    - name: add several users
      user:
        name: "{{ item }}"
        state: present
        groups: "wheel"
      with_items:
         - testuser1
         - testuser2

If you have defined a YAML list in a variables file, or the 'vars' section, you can also do::

    with_items: "{{ somelist }}"

The above would be the equivalent of::

    - name: add user testuser1
      user:
        name: "testuser1"
        state: present
        groups: "wheel"
    - name: add user testuser2
      user:
        name: "testuser2"
        state: present
        groups: "wheel"

The yum and apt modules use with_items to execute fewer package manager transactions.

Note that the types of items you iterate over with 'with_items' do not have to be simple lists of strings.
If you have a list of hashes, you can reference subkeys using things like::

    - name: add several users
      user:
        name: "{{ item.name }}"
        state: present
        groups: "{{ item.groups }}"
      with_items:
        - { name: 'testuser1', groups: 'wheel' }
        - { name: 'testuser2', groups: 'root' }

Also be aware that when combining `when` with `with_items` (or any other loop statement), the `when` statement is processed separately for each item. See :ref:`the_when_statement` for an example.

Loops are actually a combination of things `with_` + `lookup()`, so any lookup plugin can be used as a source for a loop, 'items' is lookup.

.. _nested_loops:

Nested Loops
````````````

Loops can be nested as well::

    - name: give users access to multiple databases
      mysql_user:
        name: "{{ item[0] }}"
        priv: "{{ item[1] }}.*:ALL"
        append_privs: yes
        password: "foo"
      with_nested:
        - [ 'alice', 'bob' ]
        - [ 'clientdb', 'employeedb', 'providerdb' ]

As with the case of 'with_items' above, you can use previously defined variables.::

    - name: here, 'users' contains the above list of employees
      mysql_user:
        name: "{{ item[0] }}"
        priv: "{{ item[1] }}.*:ALL"
        append_privs: yes
        password: "foo"
      with_nested:
        - "{{ users }}"
        - [ 'clientdb', 'employeedb', 'providerdb' ]

.. _looping_over_hashes:

Looping over Hashes
```````````````````

.. versionadded:: 1.5

Suppose you have the following variable::

    ---
    users:
      alice:
        name: Alice Appleworth
        telephone: 123-456-7890
      bob:
        name: Bob Bananarama
        telephone: 987-654-3210

And you want to print every user's name and phone number.  You can loop through the elements of a hash using ``with_dict`` like this::

    tasks:
      - name: Print phone records
        debug:
          msg: "User {{ item.key }} is {{ item.value.name }} ({{ item.value.telephone }})"
        with_dict: "{{ users }}"

.. _looping_over_fileglobs:

Looping over Files
``````````````````

``with_file`` iterates over the content of a list of files, `item` will be set to the content of each file in sequence.  It can be used like this::

    ---
    - hosts: all

      tasks:

        # emit a debug message containing the content of each file.
        - debug:
            msg: "{{ item }}"
          with_file:
            - first_example_file
            - second_example_file

Assuming that ``first_example_file`` contained the text "hello" and ``second_example_file`` contained the text "world", this would result in:

.. code-block:: shell-session

    TASK [debug msg={{ item }}] ******************************************************
    ok: [localhost] => (item=hello) => {
        "item": "hello",
        "msg": "hello"
    }
    ok: [localhost] => (item=world) => {
        "item": "world",
        "msg": "world"
    }

Looping over Fileglobs
``````````````````````

``with_fileglob`` matches all files in a single directory, non-recursively, that match a pattern. It calls
`Python's glob library <https://docs.python.org/2/library/glob.html>`_, and can be used like this::

    ---
    - hosts: all

      tasks:

        # first ensure our target directory exists
        - name: Ensure target directory exists
          file:
            dest: "/etc/fooapp"
            state: directory

        # copy each file over that matches the given pattern
        - name: Copy each file over that matches the given pattern
          copy:
            src: "{{ item }}"
            dest: "/etc/fooapp/"
            owner: "root"
            mode: 0600
          with_fileglob:
            - "/playbooks/files/fooapp/*"

.. note:: When using a relative path with ``with_fileglob`` in a role, Ansible resolves the path relative to the `roles/<rolename>/files` directory.


Looping over Filetrees
``````````````````````

``with_filetree`` recursively matches all files in a directory tree, enabling you to template a complete tree of files on a target system while retaining permissions and ownership.

The ``filetree`` lookup-plugin supports directories, files and symlinks, including SELinux and other file properties. Here is a complete list of what each file object consists of:

* src
* root
* path
* mode
* state
* owner
* group
* seuser
* serole
* setype
* selevel
* uid
* gid
* size
* mtime
* ctime

If you provide more than one path, it will implement a ``with_first_found`` logic, and will not process entries it already processed in previous paths. This enables the user to merge different trees in order of importance, or add role_vars specific paths to influence different instances of the same role.

Here is an example of how we use with_filetree within a role. The ``web/`` path is relative to either ``roles/<role>/files/`` or ``files/``::

    ---
    - name: Create directories
      file:
        path: /web/{{ item.path }}
        state: directory
        mode: '{{ item.mode }}'
      with_filetree: web/
      when: item.state == 'directory'

    - name: Template files
      template:
        src: '{{ item.src }}'
        dest: /web/{{ item.path }}
        mode: '{{ item.mode }}'
      with_filetree: web/
      when: item.state == 'file'

    - name: Recreate symlinks
      file:
        src: '{{ item.src }}'
        dest: /web/{{ item.path }}
        state: link
        force: yes
        mode: '{{ item.mode }}'
      with_filetree: web/
      when: item.state == 'link'


The following properties are also available:

* ``root``: allows filtering by original location
* ``path``: contains the relative path to root
* ``uidi``, ``gid``: force-create by exact id, rather than by name
* ``size``, ``mtime``, ``ctime``: filter out files by size, mtime or ctime


Looping over Parallel Sets of Data
``````````````````````````````````

Suppose you have the following variable data::

    ---
    alpha: [ 'a', 'b', 'c', 'd' ]
    numbers:  [ 1, 2, 3, 4 ]

...and you want the set of '(a, 1)' and '(b, 2)'.   Use 'with_together' to get this::

    tasks:
        - debug:
            msg: "{{ item.0 }} and {{ item.1 }}"
          with_together:
            - "{{ alpha }}"
            - "{{ numbers }}"

Looping over Subelements
````````````````````````

Suppose you want to do something like loop over a list of users, creating them, and allowing them to login by a certain set of
SSH keys.

In this example, we'll assume you have the following defined and loaded in via "vars_files" or maybe a "group_vars/all" file::

    ---
    users:
      - name: alice
        authorized:
          - /tmp/alice/onekey.pub
          - /tmp/alice/twokey.pub
        mysql:
            password: mysql-password
            hosts:
              - "%"
              - "127.0.0.1"
              - "::1"
              - "localhost"
            privs:
              - "*.*:SELECT"
              - "DB1.*:ALL"
      - name: bob
        authorized:
          - /tmp/bob/id_rsa.pub
        mysql:
            password: other-mysql-password
            hosts:
              - "db1"
            privs:
              - "*.*:SELECT"
              - "DB2.*:ALL"

You could loop over these subelements like this::

    - name: Create User
      user:
        name: "{{ item.name }}"
        state: present
        generate_ssh_key: yes
      with_items:
        - "{{ users }}"

    - name: Set authorized ssh key
      authorized_key:
        user: "{{ item.0.name }}"
        key: "{{ lookup('file', item.1) }}"
      with_subelements:
         - "{{ users }}"
         - authorized

Given the mysql hosts and privs subkey lists, you can also iterate over a list in a nested subkey::

    - name: Setup MySQL users
      mysql_user:
        name: "{{ item.0.name }}"
        password: "{{ item.0.mysql.password }}"
        host: "{{ item.1 }}"
        priv: "{{ item.0.mysql.privs | join('/') }}"
      with_subelements:
        - "{{ users }}"
        - mysql.hosts

Subelements walks a list of hashes (aka dictionaries) and then traverses a list with a given (nested sub-)key inside of those
records.

Optionally,  you can add a third element to the subelements list, that holds a
dictionary of flags. Currently you can add the 'skip_missing' flag. If set to
True, the lookup plugin will skip the lists items that do not contain the given
subkey. Without this flag, or if that flag is set to False, the plugin will
yield an error and complain about the missing subkey.

The authorized_key pattern is exactly where it comes up most.

.. _looping_over_integer_sequences:

Looping over Integer Sequences
``````````````````````````````

``with_sequence`` generates a sequence of items. You
can specify a start value, an end value, an optional "stride" value that specifies the number of steps to increment the sequence, and an optional printf-style format string.

Arguments should be specified as key=value pair strings.

A simple shortcut form of the arguments string is also accepted: ``[start-]end[/stride][:format]``.

Numerical values can be specified in decimal, hexadecimal (0x3f8) or octal (0600).
Negative numbers are not supported.  This works as follows::

    ---
    - hosts: all

      tasks:

        # create groups
        - group:
            name: "evens"
            state: present
        - group:
            name: "odds"
            state: present

        # create some test users
        - user:
            name: "{{ item }}"
            state: present
            groups: "evens"
          with_sequence: start=0 end=32 format=testuser%02x

        # create a series of directories with even numbers for some reason
        - file:
            dest: "/var/stuff/{{ item }}"
            state: directory
          with_sequence: start=4 end=16 stride=2

        # a simpler way to use the sequence plugin
        # create 4 groups
        - group:
            name: "group{{ item }}"
            state: present
          with_sequence: count=4

.. _random_choice:

Random Choices
``````````````

The 'random_choice' feature can be used to pick something at random.  While it's not a load balancer (there are modules
for those), it can somewhat be used as a poor man's load balancer in a MacGyver like situation::

    - debug:
        msg: "{{ item }}"
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

.. versionadded:: 1.4

Sometimes you would want to retry a task until a certain condition is met.  Here's an example::

    - shell: /usr/bin/foo
      register: result
      until: result.stdout.find("all systems go") != -1
      retries: 5
      delay: 10

The above example run the shell module recursively till the module's result has "all systems go" in its stdout or the task has
been retried for 5 times with a delay of 10 seconds. The default value for "retries" is 3 and "delay" is 5.

The task returns the results returned by the last task run. The results of individual retries can be viewed by -vv option.
The registered variable will also have a new key "attempts" which will have the number of the retries for the task.

.. _with_first_found:

Finding First Matched Files
```````````````````````````

.. note:: This is an uncommon thing to want to do, but we're documenting it for completeness.  You probably won't be reaching for this one often.

This isn't exactly a loop, but it's close.  What if you want to use a reference to a file based on the first file found
that matches a given criteria, and some of the filenames are determined by variable names?  Yes, you can do that as follows::

    - name: INTERFACES | Create Ansible header for /etc/network/interfaces
      template:
        src: "{{ item }}"
        dest: "/etc/foo.conf"
      with_first_found:
        - "{{ ansible_virtualization_type }}_foo.conf"
        - "default_foo.conf"

This tool also has a long form version that allows for configurable search paths.  Here's an example::

    - name: some configuration template
      template:
        src: "{{ item }}"
        dest: "/etc/file.cfg"
        mode: 0444
        owner: "root"
        group: "root"
      with_first_found:
        - files:
           - "{{ inventory_hostname }}/etc/file.cfg"
          paths:
           - ../../../templates.overwrites
           - ../../../templates
        - files:
            - etc/file.cfg
          paths:
            - templates

.. _looping_over_the_results_of_a_program_execution:

Iterating Over The Results of a Program Execution
`````````````````````````````````````````````````

.. note:: This is an uncommon thing to want to do, but we're documenting it for completeness.  You probably won't be reaching for this one often.

Sometimes you might want to execute a program, and based on the output of that program, loop over the results of that line by line.
Ansible provides a neat way to do that, though you should remember, this is always executed on the control machine, not the remote
machine::

    - name: Example of looping over a command result
      shell: "/usr/bin/frobnicate {{ item }}"
      with_lines:
        - "/usr/bin/frobnications_per_host --param {{ inventory_hostname }}"

Ok, that was a bit arbitrary.  In fact, if you're doing something that is inventory related you might just want to write a dynamic
inventory source instead (see :doc:`intro_dynamic_inventory`), but this can be occasionally useful in quick-and-dirty implementations.

Should you ever need to execute a command remotely, you would not use the above method.  Instead do this::

    - name: Example of looping over a REMOTE command result
      shell: "/usr/bin/something"
      register: command_result

    - name: Do something with each result
      shell: "/usr/bin/something_else --param {{ item }}"
      with_items:
        - "{{ command_result.stdout_lines }}"

.. _indexed_lists:

Looping Over A List With An Index
`````````````````````````````````

.. note:: This is an uncommon thing to want to do, but we're documenting it for completeness.  You probably won't be reaching for this one often.

.. versionadded:: 1.3

If you want to loop over an array and also get the numeric index of where you are in the array as you go, you can also do that.
It's uncommonly used::

    - name: indexed loop demo
      debug:
        msg: "at array position {{ item.0 }} there is a value {{ item.1 }}"
      with_indexed_items:
        - "{{ some_list }}"

.. _using_ini_with_a_loop:

Using ini file with a loop
``````````````````````````
.. versionadded:: 2.0

The ini plugin can use regexp to retrieve a set of keys. As a consequence, we can loop over this set. Here is the ini file we'll use:

.. code-block:: ini

    [section1]
    value1=section1/value1
    value2=section1/value2

    [section2]
    value1=section2/value1
    value2=section2/value2

Here is an example of using ``with_ini``::

    - debug:
        msg: "{{ item }}"
      with_ini:
        - value[1-2]
        - section: section1
        - file: "lookup.ini"
        - re: true

And here is the returned value::

    {
          "changed": false,
          "msg": "All items completed",
          "results": [
              {
                  "invocation": {
                      "module_args": "msg=\"section1/value1\"",
                      "module_name": "debug"
                  },
                  "item": "section1/value1",
                  "msg": "section1/value1",
                  "verbose_always": true
              },
              {
                  "invocation": {
                      "module_args": "msg=\"section1/value2\"",
                      "module_name": "debug"
                  },
                  "item": "section1/value2",
                  "msg": "section1/value2",
                  "verbose_always": true
              }
          ]
      }

.. _flattening_a_list:

Flattening A List
`````````````````

.. note:: This is an uncommon thing to want to do, but we're documenting it for completeness.  You probably won't be reaching for this one often.

In rare instances you might have several lists of lists, and you just want to iterate over every item in all of those lists.  Assume
a really crazy hypothetical datastructure::

    ----
    # file: roles/foo/vars/main.yml
    packages_base:
      - [ 'foo-package', 'bar-package' ]
    packages_apps:
      - [ ['one-package', 'two-package' ]]
      - [ ['red-package'], ['blue-package']]

As you can see the formatting of packages in these lists is all over the place.  How can we install all of the packages in both lists?::

    - name: flattened loop demo
      yum:
        name: "{{ item }}"
        state: present
      with_flattened:
         - "{{ packages_base }}"
         - "{{ packages_apps }}"

That's how!

.. _using_register_with_a_loop:

Using register with a loop
``````````````````````````

After using ``register`` with a loop, the data structure placed in the variable will contain a ``results`` attribute that is a list of all responses from the module.

Here is an example of using ``register`` with ``with_items``::

    - shell: "echo {{ item }}"
      with_items:
        - "one"
        - "two"
      register: echo

This differs from the data structure returned when using ``register`` without a loop::

    {
        "changed": true,
        "msg": "All items completed",
        "results": [
            {
                "changed": true,
                "cmd": "echo \"one\" ",
                "delta": "0:00:00.003110",
                "end": "2013-12-19 12:00:05.187153",
                "invocation": {
                    "module_args": "echo \"one\"",
                    "module_name": "shell"
                },
                "item": "one",
                "rc": 0,
                "start": "2013-12-19 12:00:05.184043",
                "stderr": "",
                "stdout": "one"
            },
            {
                "changed": true,
                "cmd": "echo \"two\" ",
                "delta": "0:00:00.002920",
                "end": "2013-12-19 12:00:05.245502",
                "invocation": {
                    "module_args": "echo \"two\"",
                    "module_name": "shell"
                },
                "item": "two",
                "rc": 0,
                "start": "2013-12-19 12:00:05.242582",
                "stderr": "",
                "stdout": "two"
            }
        ]
    }

Subsequent loops over the registered variable to inspect the results may look like::

    - name: Fail if return code is not 0
      fail:
        msg: "The command ({{ item.cmd }}) did not have a 0 return code"
      when: item.rc != 0
      with_items: "{{ echo.results }}"

During iteration, the result of the current item will be placed in the variable::

    - shell: echo "{{ item }}"
      with_items:
        - one
        - two
      register: echo
      changed_when: echo.stdout != "one"



.. _looping_over_the_inventory:

Looping over the inventory
``````````````````````````

If you wish to loop over the inventory, or just a subset of it, there is multiple ways.
One can use a regular ``with_items`` with the ``play_hosts`` or ``groups`` variables, like this::

    # show all the hosts in the inventory
    - debug:
        msg: "{{ item }}"
      with_items:
        - "{{ groups['all'] }}"

    # show all the hosts in the current play
    - debug:
        msg: "{{ item }}"
      with_items:
        - "{{ play_hosts }}"

There is also a specific lookup plugin ``inventory_hostnames`` that can be used like this::

    # show all the hosts in the inventory
    - debug:
        msg: "{{ item }}"
      with_inventory_hostnames:
        - all

    # show all the hosts matching the pattern, ie all but the group www
    - debug:
        msg: "{{ item }}"
      with_inventory_hostnames:
        - all:!www

More information on the patterns can be found on :doc:`intro_patterns`

.. _loop_control:

Loop Control
````````````

.. versionadded:: 2.1

In 2.0 you are again able to use `with_` loops and task includes (but not playbook includes). This adds the ability to loop over the set of tasks in one shot.
Ansible by default sets the loop variable `item` for each loop, which causes these nested loops to overwrite the value of `item` from the "outer" loops.
As of Ansible 2.1, the `loop_control` option can be used to specify the name of the variable to be used for the loop::

    # main.yml
    - include: inner.yml
      with_items:
        - 1
        - 2
        - 3
      loop_control:
        loop_var: outer_item

    # inner.yml
    - debug:
        msg: "outer item={{ outer_item }} inner item={{ item }}"
      with_items:
        - a
        - b
        - c

.. note:: If Ansible detects that the current loop is using a variable which has already been defined, it will raise an error to fail the task.

.. versionadded:: 2.2

When using complex data structures for looping the display might get a bit too "busy", this is where the C(label) directive comes to help::

    - name: create servers
      digital_ocean:
        name: "{{ item.name }}"
        state: present
      with_items:
        - name: server1
          disks: 3gb
          ram: 15Gb
          network:
            nic01: 100Gb
            nic02: 10Gb
            ...
      loop_control:
        label: "{{item.name}}"

This will now display just the 'label' field instead of the whole structure per 'item', it defaults to '"{{item}}"' to display things as usual.

.. versionadded:: 2.2

Another option to loop control is C(pause), which allows you to control the time (in seconds) between execution of items in a task loop.::

    # main.yml
    - name: create servers, pause 3s before creating next
      digital_ocean:
        name: "{{ item }}"
        state: present
      with_items:
        - server1
        - server2
      loop_control:
        pause: 3


.. _loops_and_includes_2.0:

Loops and Includes in 2.0
`````````````````````````

Because `loop_control` is not available in Ansible 2.0, when using an include with a loop you should use `set_fact` to save the "outer" loops value
for `item`::

    # main.yml
    - include: inner.yml
      with_items:
        - 1
        - 2
        - 3

    # inner.yml
    - set_fact:
        outer_item: "{{ item }}"

    - debug:
        msg: "outer item={{ outer_item }} inner item={{ item }}"
      with_items:
        - a
        - b
        - c


.. _writing_your_own_iterators:

Writing Your Own Iterators
``````````````````````````

While you ordinarily shouldn't have to, should you wish to write your own ways to loop over arbitrary data structures, you can read :doc:`dev_guide/developing_plugins` for some starter
information.  Each of the above features are implemented as plugins in ansible, so there are many implementations to reference.

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_reuse_roles`
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
