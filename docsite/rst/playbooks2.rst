Advanced Playbooks
==================

Here are some advanced features of the playbooks language.  Using all of these features
are not neccessary, but many of them will prove useful.  If a feature doesn't seem immediately
relevant, feel free to skip it.  For many people, the features documented in `playbooks` will
be 90% or more of what they use in Ansible.

.. contents::
   :depth: 2
   :backlinks: top

Tags
````

.. versionadded:: 0.6

If you have a large playbook it may become useful to be able to run a
specific part of the configuration.  Both plays and tasks support a
"tags:" attribute for this reason.

Example::

    tasks:

        - action: yum name=$item state=installed
          with_items:
             - httpd
             - memcached
          tags:
             - packages

        - action: template src=templates/src.j2 dest=/etc/foo.conf
          tags:
             - configuration

If you wanted to just run the "configuration" and "packages" part of a very long playbook, you could do this::

    ansible-playbook example.yml --tags "configuration,packages"

Playbooks Including Playbooks
`````````````````````````````

.. versionadded:: 0.6

To further advance the concept of include files, playbook files can
include other playbook files.  Suppose you define the behavior of all
your webservers in "webservers.yml" and all your database servers in
"dbservers.yml".  You can create a "site.yml" that would reconfigure
all of your systems like this::

    ----
    - include: playbooks/webservers.yml
    - include: playbooks/dbservers.yml

This concept works great with tags to rapidly select exactly what plays you want to run, and exactly
what parts of those plays.

Ignoring Failed Commands
````````````````````````

.. versionadded:: 0.6

Generally playbooks will stop executing any more steps on a host that
has a failure.  Sometimes, though, you want to continue on.  To do so,
write a task that looks like this::

    - name: this will not be counted as a failure
      action: command /bin/false
      ignore_errors: yes

Accessing Complex Variable Data
```````````````````````````````

Some provided facts, like networking information, are made available as nested data structures.  To access
them a simple '$foo' is not sufficient, but it is still easy to do.   Here's how we get an IP address::

    ${ansible_eth0.ipv4.address}

It is also possible to access variables whose elements are arrays::

    ${somelist[0]}

And the array and hash reference syntaxes can be mixed.

In templates, the simple access form still holds, but they can also be accessed from Jinja2 in more Python-native ways if
that is preferred::

    {{ ansible_eth0["ipv4"]["address"] }}

Accessing Information About Other Hosts
```````````````````````````````````````

If your database server wants to check the value of a 'fact' from another node, or an inventory variable
assigned to another node, it's easy to do so within a template or even an action line::

    ${hostvars.hostname.factname}

.. note::
   No database or other complex system is required to exchange data
   between hosts.  The hosts that you want to reference data from must
   be included in either the current play or any previous play if you
   are using a version prior to 0.8.  If you are using 0.8, and you have
   not yet contacted the host, you'll be able to read inventory variables
   but not fact variables.  Speak to the host by including it in a play
   to make fact information available.

Additionally, *group_names* is a list (array) of all the groups the current host is in.  This can be used in templates using Jinja2 syntax to make template source files that vary based on the group membership (or role) of the host::

   {% if 'webserver' in group_names %}
      # some part of a configuration file that only applies to webservers
   {% endif %}

*groups* is a list of all the groups (and hosts) in the inventory.  This can be used to enumerate all hosts within a group.
For example::

   {% for host in groups['app_servers'] %}
      # something that applies to all app servers.
   {% endfor %}

Use cases include pointing a frontend proxy server to all of the app servers, setting up the correct firewall rules between servers, etc.

*inventory_hostname* is the name of the hostname as configured in Ansible's inventory host file.  This can
be useful for when you don't want to rely on the discovered hostname `ansible_hostname` or for other mysterious
reasons.  If you have a long FQDN, *inventory_hostname_short* (in Ansible 0.6) also contains the part up to the first
period.

Don't worry about any of this unless you think you need it.  You'll know when you do.

Variable File Separation
````````````````````````

It's a great idea to keep your playbooks under source control, but
you may wish to make the playbook source public while keeping certain
important variables private.  Similarly, sometimes you may just
want to keep certain information in different files, away from
the main playbook.

You can do this by using an external variables file, or files, just like this::

    ---
    - hosts: all
      user: root
      vars:
        favcolor: blue
      vars_files:
        - /vars/external_vars.yml
      tasks:
      - name: this is just a placeholder
        action: command /bin/echo foo

This removes the risk of sharing sensitive data with others when
sharing your playbook source with them.

The contents of each variables file is a simple YAML dictionary, like this::

    ---
    # in the above example, this would be vars/external_vars.yml
    somevar: somevalue
    password: magic

.. note::
   It's also possible to keep per-host and per-group variables in very
   similar files, this is covered in :ref:`patterns`.

Prompting For Sensitive Data
````````````````````````````

You may wish to prompt the user for certain input, and can
do so with the similarly named 'vars_prompt' section.  This has uses
beyond security, for instance, you may use the same playbook for all
software releases and would prompt for a particular release version
in a push-script::

    ---
    - hosts: all
      user: root
      vars:
        from: "camelot"
      vars_prompt:
        name: "what is your name?"
        quest: "what is your quest?"
        favcolor: "what is your favorite color?"

There are full examples of both of these items in the github examples/playbooks directory.

An alternative form of vars_prompt allows for hiding input from the user, and may later support
some other options, but otherwise works equivalently::

   vars_prompt:
     - name: "some_password"
       prompt: "Enter password"
       private: yes
     - name: "release_version"
       prompt: "Product release version"
       private: no


Passing Variables On The Command Line
`````````````````````````````````````

In addition to `vars_prompt` and `vars_files`, it is possible to send variables over
the ansible command line.  This is particularly useful when writing a generic release playbook
where you may want to pass in the version of the application to deploy::

    ansible-playbook release.yml --extra-vars "version=1.23.45 other_variable=foo"

This is useful, for, among other things, setting the hosts group or the user for the playbook.

Example::

    -----
    - user: $user
      hosts: $hosts
      tasks:
         - ...

    ansible-playbook release.yml --extra-vars "hosts=vipers user=starbuck"

Conditional Execution
`````````````````````

Sometimes you will want to skip a particular step on a particular host.  This could be something
as simple as not installing a certain package if the operating system is a particular version,
or it could be something like performing some cleanup steps if a filesystem is getting full.

This is easy to do in Ansible, with the `only_if` clause, which actually is a Python expression.
Don't panic -- it's actually pretty simple::

    vars:
      favcolor: blue
      is_favcolor_blue: "'$favcolor' == 'blue'"
      is_centos: "'$facter_operatingsystem' == 'CentOS'"

    tasks:
      - name: "shutdown if my favorite color is blue"
        action: command /sbin/shutdown -t now
        only_if: '$is_favcolor_blue'

Variables from tools like `facter` and `ohai` can be used here, if installed, or you can
use variables that bubble up from ansible, which many are provided by the :ref:`setup` module.   As a reminder,
these variables are prefixed, so it's `$facter_operatingsystem`, not `$operatingsystem`.  Ansible's
built in variables are prefixed with `ansible_`.

The only_if expression is actually a tiny small bit of Python, so be sure to quote variables and make something
that evaluates to `True` or `False`.  It is a good idea to use 'vars_files' instead of 'vars' to define
all of your conditional expressions in a way that makes them very easy to reuse between plays
and playbooks.

You cannot use live checks here, like 'os.path.exists', so don't try.

It's also easy to provide your own facts if you want, which is covered in :doc:`moduledev`.  To run them, just
make a call to your own custom fact gathering module at the top of your list of tasks, and variables returned
there will be accessible to future tasks::

    tasks:
        - name: gather site specific fact data
          action: site_facts
        - action: command echo ${my_custom_fact_can_be_used_now}

One common useful trick with only_if is to key off the changed result of a last command.  As an example::

    tasks:
        - action: template src=/templates/foo.j2 dest=/etc/foo.conf
          register: last_result
        - action: command echo 'the file has changed'
          only_if: '${last_result.changed}'

$last_result is a variable set by the register directive. This assumes Ansible 0.8 and later.

In Ansible 0.8, a few shortcuts are available for testing whether a variable is defined or not::

    tasks:
        - action: command echo hi
          only_if: is_set('$some_variable')

There is a matching 'is_unset' that works the same way.  Quoting the variable inside the function is mandatory.

When combining `only_if` with `with_items`, be aware that the `only_if` statement is processed for each item.
This is a deliberate design::

    tasks:
        - action: command echo $item
          with_item: [ 0, 2, 4, 6, 8, 10 ]
          only_if: "$item > 5"

While `only_if` is a pretty good option for advanced users, it exposes more guts of the engine than we'd like, and
we can do better.  In 0.9, we will be adding `when`, which will be like a syntactic sugar for `only_if` and hide
this level of complexity -- it will numerous built in operators.

Conditional Execution (Simplified)
``````````````````````````````````

In Ansible 0.9, we realized that only_if was a bit syntactically complicated, and exposed too much Python
to the user.  As a result, the 'when' set of keywords was added.  The 'when' statements do not have
to be quoted or casted to specify types, but you should seperate any variables used with whitespace.  In
most cases users will be able to use 'when', but for more complex cases, only_if may still be required.

Here are various examples of 'when' in use.  'when' is incompatible with 'only_if' in the same task::

    - name: "do this if my favcolor is blue, and my dog is named fido"
      action: shell /bin/false
      when_string: $favcolor == 'blue' and $dog == 'fido'

    - name: "do this if my favcolor is not blue, and my dog is named fido"
      action: shell /bin/true
      when_string: $favcolor != 'blue' and $dog == 'fido'

    - name: "do this if my SSN is over 9000"
      action: shell /bin/true
      when_integer: $ssn > 9000

    - name: "do this if I have one of these SSNs"
      action: shell /bin/true
      when_integer:  $ssn in [ 8675309, 8675310, 8675311 ]

    - name: "do this if a variable named hippo is NOT defined"
      action: shell /bin/true
      when_unset: $hippo

    - name: "do this if a variable named hippo is defined"
      action: shell /bin/true
      when_set: $hippo

    - name: "do this if a variable named hippo is true"
      action: shell /bin/true
      when_boolean: $hippo

The when_boolean check will look for variables that look to be true as well, such as the string 'True' or
'true', non-zero numbers, and so on.

We also added when_changed and when_failed so users can execute tasks based on the status of previously
registered tasks.  As an example::

    - name: "register a task that might fail"
      action: shell /bin/false
      register: result
      ignore_errors: True

    - name: "do this if the registered task failed"
      action: shell /bin/true
      when_failed: $result

    - name: "register a task that might change"
      action: yum pkg=httpd state=latest
      register: result

    - name: "do this if the registered task changed"
      action: shell /bin/true
      when_changed: $result

Conditional Imports
```````````````````

Sometimes you will want to do certain things differently in a playbook based on certain criteria.
Having one playbook that works on multiple platforms and OS versions is a good example.

As an example, the name of the Apache package may be different between CentOS and Debian,
but it is easily handled with a minimum of syntax in an Ansible Playbook::

    ---
    - hosts: all
      user: root
      vars_files:
        - "vars/common.yml"
        - [ "vars/$facter_operatingsystem.yml", "vars/os_defaults.yml" ]
      tasks:
      - name: make sure apache is running
        action: service name=$apache state=running

.. note::
   The variable (`$facter_operatingsystem`) is being interpolated into
   the list of filenames being defined for vars_files.

As a reminder, the various YAML files contain just keys and values::

    ---
    # for vars/CentOS.yml
    apache: httpd
    somethingelse: 42

How does this work?  If the operating system was 'CentOS', the first file Ansible would try to import
would be 'vars/CentOS.yml', followed up by '/vars/os_defaults.yml' if that file
did not exist.   If no files in the list were found, an error would be raised.
On Debian, it would instead first look towards 'vars/Debian.yml' instead of 'vars/CentOS.yml', before
falling back on 'vars/os_defaults.yml'. Pretty simple.

To use this conditional import feature, you'll need facter or ohai installed prior to running the playbook, but
you can of course push this out with Ansible if you like::

    # for facter
    ansible -m yum -a "pkg=facter ensure=installed"
    ansible -m yum -a "pkg=ruby-json ensure=installed"

    # for ohai
    ansible -m yum -a "pkg=ohai ensure=installed"

Ansible's approach to configuration -- separating variables from tasks, keeps your playbooks
from turning into arbitrary code with ugly nested ifs, conditionals, and so on - and results
in more streamlined & auditable configuration rules -- especially because there are a
minimum of decision points to track.

Loops
`````

To save some typing, repeated tasks can be written in short-hand like so::

    - name: add user $item
      action: user name=$item state=present groups=wheel
      with_items:
         - testuser1
         - testuser2

If you have defined a YAML list in a variables file, or the 'vars' section, you can also do::

    with_items: $somelist

The above would be the equivalent of::

    - name: add user testuser1
      action: user name=testuser1 state=present groups=wheel
    - name: add user testuser2
      action: user name=testuser2 state=present groups=wheel

The yum and apt modules use with_items to execute fewer package manager transactions.

Note that the types of items you iterate over with 'with_items' do not have to be simple lists of strings.
If you have a list of hashes, you can reference subkeys using things like::

    ${item.subKeyName}

More Loops
``````````

.. versionadded: 0.8

Various 'lookup plugins' allow additional ways to iterate over data.  Ansible will have more of these
over time.  In 0.8, the only lookup plugins that comes stock are 'with_fileglob' and 'with_sequence', but
you can also write your own.

'with_fileglob' matches all files in a single directory, non-recursively, that match a pattern.  It can
be used like this::

    ----
    - hosts: all

      tasks:

        # first ensure our target directory exists
        - action: file dest=/etc/fooapp state=directory

        # copy each file over that matches the given pattern
        - action: copy src=$item dest=/etc/fooapp/ owner=root mode=600
          with_fileglob: /playbooks/files/fooapp/*

.. versionadded: 1.0

'with_sequence' generates a sequence of items in ascending numerical order. You
can specify a 'start', an 'end' value (inclusive), and a 'stride' value (to skip
some numbers of values), and a printf-style 'format' string.  It accepts
arguments both as key-value pairs and in a shortcut of the form
"[start-]end[/stride][:format]".  All numerical values can be specified in
hexadecimal (i.e. 0x3f8) or octal (i.e. 0644).  Negative numbers are not
supported.  Here is an example that leverages most of its features::

    ----
    - hosts: all

      tasks:

        # create groups
        - group: name=evens state=present

        - group: name=odds state=present

        # create 32 test users
        - user: name=$item state=present groups=odds
          with_sequence: 32/2:testuser%02x

        - user: name=$item state=present groups=evens
          with_sequence: 2-32/2:testuser%02x

        # create a series of directories for some reason
        - file: dest=/var/stuff/$item state=directory
          with_sequence: start=4 end=16

The key-value form also supports a 'count' option, which always generates
'count' entries regardless of the stride. The count option is mostly useful for
avoiding off-by-one errors and errors calculating the number of entries in a
sequence when a stride is specified.  The shortcut form cannot be used to
specify a count.  As an example::

    ----
    - hosts: all

      tasks:

        # create 4 groups
        - group: name=group${item} state=present
          with_sequence: count=4

Getting values from files
`````````````````````````

.. versionadded: 0.8

Sometimes you'll want to include the content of a file directly into a playbook.  You can do so using a macro.
This syntax will remain in future versions, though we will also will provide ways to do this via lookup plugins (see "More Loops") as well.  What follows
is an example using the authorized_key module, which requires the actual text of the SSH key as a parameter::

    tasks:
        - name: enable key-based ssh access for users
          authorized_key: user=$item key='$FILE(/keys/$item)'
          with_items:
             - pinky
             - brain
             - snowball

The "$PIPE" macro works just like file, except you would feed it a command string instead.  It executes locally, not remotely, as does $FILE.

Selecting Files And Templates Based On Variables
````````````````````````````````````````````````

Sometimes a configuration file you want to copy, or a template you will use may depend on a variable.
The following construct selects the first available file appropriate for the variables of a given host, which is often much cleaner than putting a lot of if conditionals in a template.

The following example shows how to template out a configuration file that was very different between, say, CentOS and Debian::

    - name: template a file
      action: template src=$item dest=/etc/myapp/foo.conf
      first_available_file:
        - /srv/templates/myapp/${ansible_distribution}.conf
        - /srv/templates/myapp/default.conf

first_available_file is only available to the copy and template modules.

Asynchronous Actions and Polling
````````````````````````````````

By default tasks in playbooks block, meaning the connections stay open
until the task is done on each node.  If executing playbooks with
a small parallelism value (aka ``--forks``), you may wish that long
running operations can go faster.  The easiest way to do this is
to kick them off all at once and then poll until they are done.

You will also want to use asynchronous mode on very long running
operations that might be subject to timeout.

To launch a task asynchronously, specify its maximum runtime
and how frequently you would like to poll for status.  The default
poll value is 10 seconds if you do not specify a value for `poll`::

    ---
    - hosts: all
      user: root
      tasks:
      - name: simulate long running op (15 sec), wait for up to 45, poll every 5
        action: command /bin/sleep 15
        async: 45
        poll: 5

.. note::
   There is no default for the async time limit.  If you leave off the
   'async' keyword, the task runs synchronously, which is Ansible's
   default.

Alternatively, if you do not need to wait on the task to complete, you may
"fire and forget" by specifying a poll value of 0::

    ---
    - hosts: all
      user: root
      tasks:
      - name: simulate long running op, allow to run for 45, fire and forget
        action: command /bin/sleep 15
        async: 45
        poll: 0

.. note::
   You shouldn't "fire and forget" with operations that require
   exclusive locks, such as yum transactions, if you expect to run other
   commands later in the playbook against those same resources.

.. note::
   Using a higher value for ``--forks`` will result in kicking off asynchronous
   tasks even faster.  This also increases the efficiency of polling.

Local Playbooks
```````````````

It may be useful to use a playbook locally, rather than by connecting over SSH.  This can be useful
for assuring the configuration of a system by putting a playbook on a crontab.  This may also be used
to run a playbook inside a OS installer, such as an Anaconda kickstart.

To run an entire playbook locally, just set the "hosts:" line to "hosts:127.0.0.1" and then run the playbook like so::

    ansible-playbook playbook.yml --connection=local

Alternatively, a local connection can be used in a single playbook play, even if other plays in the playbook
use the default remote connection type::

    hosts: 127.0.0.1
    connection: local

Turning Off Facts
`````````````````

If you know you don't need any fact data about your hosts, and know everything about your systems centrally, you
can turn off fact gathering.  This has advantages in scaling ansible in push mode with very large numbers of
systems, mainly, or if you are using Ansible on experimental platforms.   In any play, just do this::

    - hosts: whatever
      gather_facts: no

Pull-Mode Playbooks
```````````````````

The use of playbooks in local mode (above) is made extremely powerful with the addition of `ansible-pull`.
A script for setting up ansible-pull is provided in the examples/playbooks directory of the source
checkout.

The basic idea is to use Ansible to set up a remote copy of ansible on each managed node, each set to run via
cron and update playbook source via git.  This inverts the default push architecture of ansible into a pull
architecture, which has near-limitless scaling potential.  The setup playbook can be tuned to change
the cron frequency, logging locations, and parameters to ansible-pull.

This is useful both for extreme scale-out as well as periodic remediation.  Usage of the 'fetch' module to retrieve
logs from ansible-pull runs would be an excellent way to gather and analyze remote logs from ansible-pull.

Register Variables
``````````````````

.. versionadded:: 0.7

Often in a playbook it may be useful to store the result of a given command in a variable and access
it later.  Use of the command module in this way can in many ways eliminate the need to write site specific facts, for
instance, you could test for the existance of a particular program.

The 'register' keyword decides what variable to save a result in.  The resulting variables can be used in templates, action lines, or only_if statements.  It looks like this (in an obviously trivial example)::

    - name: test play
      hosts: all

      tasks:

          - action: shell cat /etc/motd
            register: motd_contents

          - action: shell echo "motd contains the word hi"
            only_if: "'${motd_contents.stdout}'.find('hi') != -1"


Rolling Updates
```````````````

.. versionadded:: 0.7

By default ansible will try to manage all of the machines referenced in a play in parallel.  For a rolling updates
use case, you can define how many hosts ansible should manage at a single time by using the ''serial'' keyword::


    - name: test play
      hosts: webservers
      serial: 3

In the above example, if we had 100 hosts, 3 hosts in the group 'webservers'
would complete the play completely before moving on to the next 3 hosts.

Delegation
``````````

.. versionadded:: 0.7

If you want to perform a task on one host with reference to other hosts, use the 'delegate_to' keyword on a task.
This is ideal for placing nodes in a load balanced pool, or removing them.  It is also very useful for controlling
outage windows.  Using this with the 'serial' keyword to control the number of hosts executing at one time is also
a good idea::

    ---
    - hosts: webservers
      serial: 5

      tasks:
      - name: take out of load balancer pool
        action: command /usr/bin/take_out_of_pool $inventory_hostname
        delegate_to: 127.0.0.1

      - name: actual steps would go here
        action: yum name=acme-web-stack state=latest

      - name: add back to load balancer pool
        action: command /usr/bin/add_back_to_pool $inventory_hostname
        delegate_to: 127.0.0.1


Here is the same playbook as above, but using the shorthand syntax,
'local_action', for delegating to 127.0.0.1::

    ---
    # ...
      tasks:
      - name: take out of load balancer pool
        local_action: command /usr/bin/take_out_of_pool $inventory_hostname

    # ...

      - name: add back to load balancer pool
        local_action: command /usr/bin/add_back_to_pool $inventory_hostname

Fireball Mode
`````````````

.. versionadded:: 0.8

Ansible's core connection types of 'local', 'paramiko', and 'ssh' are augmented in version 0.8 and later by a new extra-fast
connection type called 'fireball'.  It can only be used with playbooks and does require some additional setup
outside the lines of ansible's normal "no bootstrapping" philosophy.  You are not required to use fireball mode
to use Ansible, though some users may appreciate it.

Fireball mode works by launching a temporary 0mq daemon from SSH that by default lives for only 30 minutes before
shutting off.  Fireball mode once running uses temporary AES keys to encrypt a session, and requires direct
communication to given nodes on the configured port.  The default is 5099.  The fireball daemon runs as any user you
set it down as.  So it can run as you, root, or so on.  If multiple users are running Ansible as the same batch of hosts,
take care to use unique ports.

Fireball mode is roughly 10 times faster than paramiko for communicating with nodes and may be a good option
if you have a large number of hosts::

    ---

    # set up the fireball transport
    - hosts: all
      gather_facts: no
      connection: ssh # or paramiko
      sudo: yes
      tasks:
          - action: fireball

    # these operations will occur over the fireball transport
    - hosts: all
      connection: fireball
      tasks:
          - action: shell echo "Hello ${item}"
            with_items:
                - one
                - two

In order to use fireball mode, certain dependencies must be installed on both ends.   You can use this playbook as a basis for initial bootstrapping on
any platform.  You will also need gcc and zeromq-devel installed from your package manager, which you can of course also get Ansible to install::

    ---
    - hosts: all
      sudo: yes
      gather_facts: no
      connection: ssh
      tasks:
          - action: easy_install name=pip
          - action: pip name=$item state=present
            with_items:
              - pyzmq
              - pyasn1
              - PyCrypto
              - python-keyczar

Fedora and EPEL also have Ansible RPM subpackages available for fireball-dependencies.

Also see the module documentation section.


Understanding Variable Precedence
`````````````````````````````````

You have already learned about inventory host and group variables, 'vars', and 'vars_files'.

If a variable name is defined in more than one place with the same name, priority is as follows
to determine which place sets the value of the variable.

1.  Variables loaded from YAML files mentioned in 'vars_files' in a playbook.

2.  facts, whether built in or custom, or variables assigned from the 'register' keyword.

3.  variables passed to parameterized task include statements.

4.  'vars' as defined in the playbook.

5.  Host variables from inventory.

6.  Group variables from inventory, in order of least specific group to most specific.

Therefore, if you want to set a default value for something you wish to override somewhere else, the best
place to set such a default is in a group variable.

Style Points
````````````

Ansible playbooks are colorized.  If you do not like this, set the ANSIBLE_NOCOLOR=1 environment variable.

Ansible playbooks also look more impressive with cowsay installed, and we encourage installing this package.

.. seealso::

   :doc:`YAMLSyntax`
       Learn about YAML syntax
   :doc:`playbooks`
       Review the basic playbook features
   :doc:`bestpractices`
       Various tips about playbooks in the real world
   :doc:`modules`
       Learn about available modules
   :doc:`moduledev`
       Learn how to extend Ansible by writing your own modules
   :doc:`patterns`
       Learn about how to select hosts
   `Github examples directory <https://github.com/ansible/ansible/tree/devel/examples/playbooks>`_
       Complete playbook files from the github project source
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups


