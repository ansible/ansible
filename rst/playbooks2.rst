Advanced Playbooks
==================

Here are some advanced features of the playbooks language.  Using all of these features
are not neccessary, but many of them will prove useful.  If a feature doesn't seem immediately
relevant, feel free to skip it.  For many people, the features documented in `playbooks` will
be 90% or more of what they use in Ansible.

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

.. deprecated:: 0.6

Generally playbooks will stop executing any more steps on a host that
has a failure.  Sometimes, though, you want to continue on.  To do so,
write a task that looks like this::

    - name: this will not be counted as a failure
      action: command /bin/false
      ignore_errors: True

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
   be included in either the current play or any previous play.

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

Variable File Seperation
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
       private: True
     - name: "release_version"
       prompt: "Product release version"
       private: False


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

Ansible's approach to configuration -- seperating variables from tasks, keeps your playbooks
from turning into arbitrary code with ugly nested ifs, conditionals, and so on - and results
in more streamlined & auditable configuration rules -- especially because there are a 
minimum of decision points to track.

Loop Shorthand
``````````````

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

In a future release, the yum and apt modules will use with_items to execute fewer package
manager transactions.


Selecting Files And Templates Based On Variables
````````````````````````````````````````````````

Sometimes a configuration file you want to copy, or a template you will use may depend on a variable.
The following construct selects the first available file appropriate for the variables of a given host,
which is often much cleaner than putting a lot of if conditionals in a template.

The following example shows how to template out a configuration file that was very different between, say,
CentOS and Debian::

    - name: template a file
      action: template src=$item dest=/etc/myapp/foo.conf
      first_available_file:
        - /srv/templates/myapp/${ansible_distribution}.conf
        - /srv/templates/myapp/default.conf


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
      gather_facts: False

Pull-Mode Playbooks
```````````````````

The use of playbooks in local mode (above) is made extremely powerful with the addition of `ansible-pull`.
A script for setting up ansible-pull is provided in the examples/playbooks directory of the source
checkout.

The basic idea is to use Ansible to set up a remote copy of ansible on each managed node, each set to run via
cron and update playbook source via git.  This interverts the default push architecture of ansible into a pull
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


