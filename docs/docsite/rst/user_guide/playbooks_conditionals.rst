.. _playbooks_conditionals:

Conditionals
============

.. contents:: Topics


Often the result of a play may depend on the value of a variable, fact (something learned about the remote system), or previous task result.
In some cases, the values of variables may depend on other variables.
Additional groups can be created to manage hosts based on whether the hosts match other criteria. This topic covers how conditionals are used in playbooks.

.. note:: There are many options to control execution flow in Ansible. More examples of supported conditionals can be located here: http://jinja.pocoo.org/docs/dev/templates/#comparisons.


.. _the_when_statement:

The When Statement
``````````````````

Sometimes you will want to skip a particular step on a particular host.
This could be something as simple as not installing a certain package if the operating system is a particular version,
or it could be something like performing some cleanup steps if a filesystem is getting full.

This is easy to do in Ansible with the `when` clause, which contains a raw Jinja2 expression without double curly braces (see :doc:`playbooks_variables`).
It's actually pretty simple::

    tasks:
      - name: "shut down Debian flavored systems"
        command: /sbin/shutdown -t now
        when: ansible_os_family == "Debian"
        # note that Ansible facts and vars like ansible_os_family can be used
        # directly in conditionals without double curly braces

You can also use parentheses to group conditions::

    tasks:
      - name: "shut down CentOS 6 and Debian 7 systems"
        command: /sbin/shutdown -t now
        when: (ansible_distribution == "CentOS" and ansible_distribution_major_version == "6") or
              (ansible_distribution == "Debian" and ansible_distribution_major_version == "7")

Multiple conditions that all need to be true (a logical 'and') can also be specified as a list::

    tasks:
      - name: "shut down CentOS 6 systems"
        command: /sbin/shutdown -t now
        when:
          - ansible_distribution == "CentOS"
          - ansible_distribution_major_version == "6"

A number of Jinja2 "filters" can also be used in when statements, some of which are unique
and provided by Ansible.  Suppose we want to ignore the error of one statement and then
decide to do something conditionally based on success or failure::

    tasks:
      - command: /bin/false
        register: result
        ignore_errors: True

      - command: /bin/something
        when: result is failed

      # In older versions of ansible use ``success``, now both are valid but succeeded uses the correct tense.
      - command: /bin/something_else
        when: result is succeeded

      - command: /bin/still/something_else
        when: result is skipped


.. note:: both `success` and `succeeded` work (`fail`/`failed`, etc).


As a reminder, to see what facts are available on a particular system, you can do the following::

    ansible hostname.example.com -m setup

Tip: Sometimes you'll get back a variable that's a string and you'll want to do a math operation comparison on it.  You can do this like so::

    tasks:
      - shell: echo "only on Red Hat 6, derivatives, and later"
        when: ansible_os_family == "RedHat" and ansible_lsb.major_release|int >= 6

.. note:: the above example requires the lsb_release package on the target host in order to return the ansible_lsb.major_release fact.

Variables defined in the playbooks or inventory can also be used.  An example may be the execution of a task based on a variable's boolean value::

    vars:
      epic: true

Then a conditional execution might look like::

    tasks:
        - shell: echo "This certainly is epic!"
          when: epic

or::

    tasks:
        - shell: echo "This certainly isn't epic!"
          when: not epic

If a required variable has not been set, you can skip or fail using Jinja2's `defined` test. For example::

    tasks:
        - shell: echo "I've got '{{ foo }}' and am not afraid to use it!"
          when: foo is defined

        - fail: msg="Bailing out. this play requires 'bar'"
          when: bar is undefined

This is especially useful in combination with the conditional import of vars files (see below).
As the examples show, you don't need to use `{{ }}` to use variables inside conditionals, as these are already implied.

.. _loops_and_conditionals:

Loops and Conditionals
``````````````````````
Combining `when` with loops (see :doc:`playbooks_loops`), be aware that the `when` statement is processed separately for each item. This is by design::

    tasks:
        - command: echo {{ item }}
          loop: [ 0, 2, 4, 6, 8, 10 ]
          when: item > 5

If you need to skip the whole task depending on the loop variable being defined, used the `|default` filter to provide an empty iterator::

        - command: echo {{ item }}
          loop: "{{ mylist|default([]) }}"
          when: item > 5


If using a dict in a loop::

        - command: echo {{ item.key }}
          loop: "{{ query('dict', mydict|default({})) }}"
          when: item.value > 5

.. _loading_in_custom_facts:

Loading in Custom Facts
```````````````````````

It's also easy to provide your own facts if you want, which is covered in :ref:`developing_modules`.  To run them, just
make a call to your own custom fact gathering module at the top of your list of tasks, and variables returned
there will be accessible to future tasks::

    tasks:
        - name: gather site specific fact data
          action: site_facts
        - command: /usr/bin/thingy
          when: my_custom_fact_just_retrieved_from_the_remote_system == '1234'

.. _when_roles_and_includes:

Applying 'when' to roles, imports, and includes
```````````````````````````````````````````````

Note that if you have several tasks that all share the same conditional statement, you can affix the conditional
to a task include statement as below.  All the tasks get evaluated, but the conditional is applied to each and every task::

    - import_tasks: tasks/sometasks.yml
      when: "'reticulating splines' in output"

.. note:: In versions prior to 2.0 this worked with task includes but not playbook includes.  2.0 allows it to work with both.

Or with a role::

    - hosts: webservers
      roles:
         - role: debian_stock_config
           when: ansible_os_family == 'Debian'

You will note a lot of 'skipped' output by default in Ansible when using this approach on systems that don't match the criteria.
Read up on the 'group_by' module in the :doc:`modules` docs for a more streamlined way to accomplish the same thing.

When used with `include_*` tasks instead of imports, the conditional is applied _only_ to the include task itself and not any other
tasks within the included file(s). A common situation where this distinction is important is as follows::

    # include a file to define a variable when it is not already defined

    # main.yml
    - include_tasks: other_tasks.yml
      when: x is not defined

    # other_tasks.yml
    - set_fact:
        x: foo
    - debug:
        var: x

In the above example, if ``import_tasks`` had been used instead both included tasks would have also been skipped. With ``include_tasks``
instead, the tasks are executed as expected because the conditional is not applied to them.

.. _conditional_imports:

Conditional Imports
```````````````````

.. note:: This is an advanced topic that is infrequently used.

Sometimes you will want to do certain things differently in a playbook based on certain criteria.
Having one playbook that works on multiple platforms and OS versions is a good example.

As an example, the name of the Apache package may be different between CentOS and Debian,
but it is easily handled with a minimum of syntax in an Ansible Playbook::

    ---
    - hosts: all
      remote_user: root
      vars_files:
        - "vars/common.yml"
        - [ "vars/{{ ansible_os_family }}.yml", "vars/os_defaults.yml" ]
      tasks:
      - name: make sure apache is started
        service: name={{ apache }} state=started

.. note::
   The variable 'ansible_os_family' is being interpolated into
   the list of filenames being defined for vars_files.

As a reminder, the various YAML files contain just keys and values::

    ---
    # for vars/RedHat.yml
    apache: httpd
    somethingelse: 42

How does this work?  For Red Hat operating systems ('CentOS', for example), the first file Ansible tries to import
is 'vars/RedHat.yml'. If that file does not exist, Ansible attempts to load 'vars/os_defaults.yml'. If no files in 
the list were found, an error is raised.

On Debian, Ansible first looks for 'vars/Debian.yml' instead of 'vars/RedHat.yml', before
falling back on 'vars/os_defaults.yml'.

Ansible's approach to configuration -- separating variables from tasks, keeping your playbooks
from turning into arbitrary code with nested conditionals - results in more streamlined and auditable configuration rules because there are fewer decision points to track.

Selecting Files And Templates Based On Variables
````````````````````````````````````````````````

.. note:: This is an advanced topic that is infrequently used.  You can probably skip this section.

Sometimes a configuration file you want to copy, or a template you will use may depend on a variable.
The following construct selects the first available file appropriate for the variables of a given host, which is often much cleaner than putting a lot of if conditionals in a template.

The following example shows how to template out a configuration file that was very different between, say, CentOS and Debian::

    - name: template a file
      template:
          src: "{{ item }}"
          dest: /etc/myapp/foo.conf
      loop: "{{ query('first_found', { 'files': myfiles, 'paths': mypaths}) }}"
      vars:
        myfiles:
          - "{{ansible_distribution}}.conf"
          -  default.conf
        mypaths: ['search_location_one/somedir/', '/opt/other_location/somedir/']

Register Variables
``````````````````

Often in a playbook it may be useful to store the result of a given command in a variable and access
it later.  Use of the command module in this way can in many ways eliminate the need to write site specific facts, for
instance, you could test for the existence of a particular program.

The 'register' keyword decides what variable to save a result in.  The resulting variables can be used in templates, action lines, or *when* statements.  It looks like this (in an obviously trivial example)::

    - name: test play
      hosts: all

      tasks:

          - shell: cat /etc/motd
            register: motd_contents

          - shell: echo "motd contains the word hi"
            when: motd_contents.stdout.find('hi') != -1

As shown previously, the registered variable's string contents are accessible with the 'stdout' value.
The registered result can be used in the loop of a task if it is converted into
a list (or already is a list) as shown below.  "stdout_lines" is already available on the object as
well though you could also call "home_dirs.stdout.split()" if you wanted, and could split by other
fields::

    - name: registered variable usage as a loop list
      hosts: all
      tasks:

        - name: retrieve the list of home directories
          command: ls /home
          register: home_dirs

        - name: add home dirs to the backup spooler
          file:
            path: /mnt/bkspool/{{ item }}
            src: /home/{{ item }}
            state: link
          loop: "{{ home_dirs.stdout_lines }}"
          # same as loop: "{{ home_dirs.stdout.split() }}"


As shown previously, the registered variable's string contents are accessible with the 'stdout' value.
You may check the registered variable's string contents for emptiness::

    - name: check registered variable for emptiness
      hosts: all

      tasks:

          - name: list contents of directory
            command: ls mydir
            register: contents

          - name: check contents for emptiness
            debug: 
              msg: "Directory is empty"
            when: contents.stdout == ""

Commonly Used Facts
```````````````````

The following Facts are frequently used in Conditionals - see above for examples.

.. _ansible_distribution:

ansible_distribution
--------------------

Possible values::

    Alpine
    Altlinux
    Amazon
    Archlinux
    ClearLinux
    Coreos
    Debian
    Fedora
    Gentoo
    Mandriva
    NA
    OpenWrt
    OracleLinux
    RedHat
    Slackware
    SMGL
    SUSE
    VMwareESX

.. See `OSDIST_LIST`

.. _ansible_distribution_major_version:

ansible_distribution_major_version
----------------------------------

This will be the major version of the operating system. For example, the value will be `16` for Ubuntu 16.04.

.. _ansible_os_family:

ansible_os_family
-----------------

Possible values::

    AIX
    Alpine
    Altlinux
    Archlinux
    Darwin
    Debian
    FreeBSD
    Gentoo
    HP-UX
    Mandrake
    RedHat
    SGML
    Slackware
    Solaris
    Suse

.. See `OS_FAMILY_MAP`

.. seealso::

   :ref:`working_with_playbooks`
       An introduction to playbooks
   :ref:`playbooks_reuse_roles`
       Playbook organization by roles
   :ref:`playbooks_best_practices`
       Best practices in playbooks
   :ref:`playbooks_variables`
       All about variables
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
