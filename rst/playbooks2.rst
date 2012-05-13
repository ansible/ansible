Advanced Playbooks
==================

Here are some advanced features of the playbooks language.  Using all of these features
are not neccessary, but many of them will prove useful.

Local Playbooks
+++++++++++++++

It may be useful to use a playbook locally, rather than by connecting over SSH.  This can be useful
for assuring the configuration of a system by putting a playbook on a crontab.  This may also be used
to run a playbook inside a OS installer, such as an Anaconda kickstart.

To run an entire playbook locally, just set the "hosts:" line to "hosts:127.0.0.1" and then run the playbook like so::

    ansible-playbook playbook.yml --connection=local

Alternatively, a local connection can be used in a single playbook play, even if other plays in the playbook
use the default remote connection type::

    hosts: 127.0.0.1
    connection: local

Pull-Mode Playbooks
+++++++++++++++++++

The use of playbooks in local mode (above) is made extremely powerful with the addition of `ansible-pull` in the
0.4 release.   A script for setting up ansible-pull is provided in the examples/playbooks directory of the source
checkout.

The basic idea is to use Ansible to set up a remote copy of ansible on each managed node, each set to run via
cron and update playbook source via git.  This interverts the default push architecture of ansible into a pull
architecture, which has near-limitless scaling potential.  The setup playbook can be tuned to change
the cron frequency, logging locations, and parameters to ansible-pull.

Accessing Hash and Array Variable Data
++++++++++++++++++++++++++++++++++++++

Some provided facts, like networking information, are made available as nested datastructures.  To access
them a simple '$foo' is not sufficient, but it is still easy to do.   Here's how we get an IP address using
Ansible 0.4 and later::

    ${ansible_eth0.ipv4.address}

It is also possible to access variables whose elements are arrays::

    ${somelist[1]}

And the array and hash reference syntaxes can be mixed.

Accessing Variables From Other Hosts
++++++++++++++++++++++++++++++++++++

If your database server wants to check the value of a 'fact' from another node, or an inventory variable
assigned to another node, it's easy to do so within a template or even an action line (note: this uses syntax available in 0.4 and later)::

    ${hostvars.hostname.factname}

NOTE: No database or other complex system is required to exchange data between hosts.  The hosts that you
want to reference data from must be included in either the current play or any previous play.

External Variables and Prompted or Sensitive Data
+++++++++++++++++++++++++++++++++++++++++++++++++

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

Prompting For Sensitive Data
++++++++++++++++++++++++++++

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

Passing Variables On The Command Line
+++++++++++++++++++++++++++++++++++++

In addition to `vars_prompt` and `vars_files`, it is possible to send variables over
the ansible command line.  This is particularly useful when writing a generic release playbook
where you may want to pass in the version of the application to deploy::

    ansible-playbook release.yml --extra-vars "version=1.23.45 other_variable=foo"

Conditional Execution
+++++++++++++++++++++

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
use variables that bubble up from ansible (0.3 and later).   As a reminder,
these variables are prefixed, so it's `$facter_operatingsystem`, not `$operatingsystem`.  Ansible's
built in variables are prefixed with `ansible_`. The only_if
expression is actually a tiny small bit of Python, so be sure to quote variables and make something
that evaluates to `True` or `False`.  It is a good idea to use 'vars_files' instead of 'vars' to define
all of your conditional expressions in a way that makes them very easy to reuse between plays
and playbooks.


Conditional Imports
+++++++++++++++++++

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

Note that a variable (`$facter_operatingsystem`) is being interpolated into the list of
filenames being defined for vars_files.

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


Using Includes To Assign Classes of Systems
+++++++++++++++++++++++++++++++++++++++++++

Include files are really powerful when used to reuse logic between playbooks.  You
could imagine a playbook describing your entire infrastructure like
this, in a list of just a few plays::

    ---

    - hosts: atlanta-webservers

      vars:
        datacenter: atlanta
        database: db.atlanta.com

      tasks:
      - include: tasks/base.yml
      - include: tasks/webservers.yml 

      handlers:
        - include: handlers/common.yml

    - hosts: atlanta-dbservers

      vars:
        datacenter: atlanta

      tasks:
      - include: tasks/base.yml
      - include: tasks/dbservers.yml

      handlers:
        - include: handlers/common.yml

There is one (or more) play defined for each group of systems, and
each play maps each group to several includes.  These includes represent
'class definitions', telling the systems what they are supposed to do or be.
In the above example, all hosts get the base configuration first and further
customize it depending on what class or nature of machines they are.


Loop Shorthand
++++++++++++++

To save some typing, repeated tasks can be written in short-hand like so::

    - name: add user $item
      action: user name=$item state=present groups=wheel
      with_items:
         - testuser1
         - testuser2

The above would be the equivalent of::

    - name: add user testuser1
      action: user name=testuser1 state=present groups=wheel
    - name: add user testuser2
      action: user name=testuser2 state=present groups=wheel

In a future release, the yum and apt modules will use with_items to execute fewer package
manager transactions.


Selecting Files And Templates Based On Variables
++++++++++++++++++++++++++++++++++++++++++++++++

Sometimes a configuration file you want to copy, or a template you will use may depend on a variable.
The following construct (new in 0.4) selects the first available file appropriate for the variables of a given host,
which is often much cleaner than putting a lot of if conditionals in a template.

The following example shows how to template out a configuration file that was very different between, say,
CentOS and Debian.

    - name: template a file
      action: template src=$item dest=/etc/myapp/foo.conf
      first_available_file:
          - /srv/templates/myapp/${ansible_distribution}.conf
          - /srv/templates/myapp/default.conf


Asynchronous Actions and Polling
++++++++++++++++++++++++++++++++

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

.. seealso::

   :doc:`YAMLSyntax`
       Learn about YAML syntax
   :doc:`playbooks`
       Review the basic playbook features
   :doc:`modules`
       Learn about available modules
   :doc:`moduledev`
       Learn how to extend Ansible by writing your own modules
   :doc:`patterns`
       Learn about how to select hosts
   `Github examples directory <https://github.com/ansible/ansible/tree/master/examples/playbooks>`_
       Complete playbook files from the github project source
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups


