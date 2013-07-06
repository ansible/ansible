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

        - action: yum name={{ item }} state=installed
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

    ---
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

Ignoring Changes
````````````````

.. versionadded:: 1.3

When a task make some changes or sometimes is simply executed, it
is reported as changed.  You may want to override this.  To do so,
write a task that looks like this::

    - name: this will not be counted as changed
      action: command /bin/true
      ignore_changed: yes

Accessing Complex Variable Data
```````````````````````````````

Some provided facts, like networking information, are made available as nested data structures.  To access
them a simple {{ foo }} is not sufficient, but it is still easy to do.   Here's how we get an IP address::

    {{ ansible_eth0["ipv4"]["address"] }}

Similarly, this is how we access the first element of an array:

    {{ foo[0] }}

Magic Variables, and How To Access Information About Other Hosts
````````````````````````````````````````````````````````````````

Even if you didn't define them yourself, ansible provides a few variables for you, automatically.
The most important of these are 'hostvars', 'group_names', and 'groups'.  Users should not use
these names themselves as they are reserved.  'environment' is also reserved.

Hostvars lets you ask about the variables of another host, including facts that have been gathered
about that host.  If, at this point, you haven't talked to that host yet in any play in the playbook
or set of playbooks, you can get at the variables, but you will not be able to see the facts.

If your database server wants to use the value of a 'fact' from another node, or an inventory variable
assigned to another node, it's easy to do so within a template or even an action line::

    {{ hostvars['test.example.com']['ansible_distribution'] }}

Additionally, *group_names* is a list (array) of all the groups the current host is in.  This can be used in templates using Jinja2 syntax to make template source files that vary based on the group membership (or role) of the host::

   {% if 'webserver' in group_names %}
      # some part of a configuration file that only applies to webservers
   {% endif %}

*groups* is a list of all the groups (and hosts) in the inventory.  This can be used to enumerate all hosts within a group.
For example::

   {% for host in groups['app_servers'] %}
      # something that applies to all app servers.
   {% endfor %}

A frequently used idiom is walking a group to find all IP addresses in that group::

   {% for host in groups['app_servers'] %}
      {{ hostvars[host]['ansible_eth0']['ipv4']['address'] }}
   {% endfor %}

An example of this could include pointing a frontend proxy server to all of the app servers, setting up the correct firewall rules between servers, etc.

Just a few other 'magic' variables are available...  There aren't many.

Additionally, *inventory_hostname* is the name of the hostname as configured in Ansible's inventory host file.  This can
be useful for when you don't want to rely on the discovered hostname `ansible_hostname` or for other mysterious
reasons.  If you have a long FQDN, *inventory_hostname_short* also contains the part up to the first
period, without the rest of the domain.

Don't worry about any of this unless you think you need it.  You'll know when you do.

Also available, *inventory_dir* is the pathname of the directory holding Ansible's inventory host file.

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

If you have a variable that changes infrequently, it might make sense to
provide a default value that can be overriden.  This can be accomplished using
the default argument::

   vars_prompt:
     - name: "release_version"
       prompt: "Product release version"
       default: "1.0"

An alternative form of vars_prompt allows for hiding input from the user, and may later support
some other options, but otherwise works equivalently::

   vars_prompt:
     - name: "some_password"
       prompt: "Enter password"
       private: yes
     - name: "release_version"
       prompt: "Product release version"
       private: no

If `Passlib <http://pythonhosted.org/passlib/>`_ is installed, vars_prompt can also crypt the
entered value so you can use it, for instance, with the user module to define a password::

   vars_prompt:
     - name: "my_password2"
       prompt: "Enter password2"
       private: yes
       encrypt: "md5_crypt"
       confirm: yes
       salt_size: 7

You can use any crypt scheme supported by 'Passlib':

- *des_crypt* - DES Crypt
- *bsdi_crypt* - BSDi Crypt
- *bigcrypt* - BigCrypt
- *crypt16* - Crypt16
- *md5_crypt* - MD5 Crypt
- *bcrypt* - BCrypt
- *sha1_crypt* - SHA-1 Crypt
- *sun_md5_crypt* - Sun MD5 Crypt
- *sha256_crypt* - SHA-256 Crypt
- *sha512_crypt* - SHA-512 Crypt
- *apr_md5_crypt* - Apache’s MD5-Crypt variant
- *phpass* - PHPass’ Portable Hash
- *pbkdf2_digest* - Generic PBKDF2 Hashes
- *cta_pbkdf2_sha1* - Cryptacular’s PBKDF2 hash
- *dlitz_pbkdf2_sha1* - Dwayne Litzenberger’s PBKDF2 hash
- *scram* - SCRAM Hash
- *bsd_nthash* - FreeBSD’s MCF-compatible nthash encoding

However, the only parameters accepted are 'salt' or 'salt_size'. You can use you own salt using
'salt', or have one generated automatically using 'salt_size'. If nothing is specified, a salt
of size 8 will be generated.

Passing Variables On The Command Line
`````````````````````````````````````

In addition to `vars_prompt` and `vars_files`, it is possible to send variables over
the ansible command line.  This is particularly useful when writing a generic release playbook
where you may want to pass in the version of the application to deploy::

    ansible-playbook release.yml --extra-vars "version=1.23.45 other_variable=foo"

This is useful, for, among other things, setting the hosts group or the user for the playbook.

Example::

    ---
    - user: '{{ user }}'
      hosts: '{{ hosts }}'
      tasks:
         - ...

    ansible-playbook release.yml --extra-vars "hosts=vipers user=starbuck"

As of Ansible 1.2, you can also pass in extra vars as quoted JSON, like so::

    --extra-vars "{'pacman':'mrs','ghosts':['inky','pinky','clyde','sue']}"

The key=value form is obviously simpler, but it's there if you need it!


Conditional Execution
`````````````````````

(Note: this section covers 1.2 conditionals, if you are using a previous version, select
the previous version of the documentation, `Ansible 1.1 Docs <http://www.ansibleworks.com/docs/released/1.1/>`_ .
Those conditional forms continue to be operational in 1.2, although the new mechanisms are cleaner.)

Sometimes you will want to skip a particular step on a particular host.  This could be something
as simple as not installing a certain package if the operating system is a particular version,
or it could be something like performing some cleanup steps if a filesystem is getting full.

This is easy to do in Ansible, with the `when` clause, which actually is a Python expression.
Don't panic -- it's actually pretty simple::

    tasks:
      - name: "shutdown Debian flavored systems"
        action: command /sbin/shutdown -t now
        when: ansible_os_family == "Debian"

A number of Jinja2 "filters" can also be used in when statements, some of which are unique
and provided by ansible.  Suppose we want to ignore the error of one statement and then
decide to do something conditionally based on success or failure::

    tasks:
      - action: command /bin/false
        register: result
        ignore_errors: True
      - action: command /bin/something
        when: result|failed
      - action: command /bin/something_else
        when: result|success


As a reminder, to see what derived variables are available, you can do::

    ansible hostname.example.com -m setup

Tip: Sometimes you'll get back a variable that's a string and you'll want to do a comparison on it.  You can do this like so:

    tasks:
      - shell: echo "only on Red Hat 6, derivatives, and later"
        when: ansible_os_family == "RedHat" and ansible_lsb.major_release|int >= 6

Variables defined in the playbooks or inventory can also be used.

If a required variable has not been set, you can skip or fail using Jinja2's
`defined` test. For example::

    tasks:
        - shell: echo "I've got '{{ foo }}' and am not afraid to use it!"
          when: foo is defined

        - fail: msg="Bailing out: this play requires 'bar'"
          when: bar is not defined

This is especially useful in combination with the conditional import of vars
files (see below).

It's also easy to provide your own facts if you want, which is covered in :doc:`moduledev`.  To run them, just
make a call to your own custom fact gathering module at the top of your list of tasks, and variables returned
there will be accessible to future tasks::

    tasks:
        - name: gather site specific fact data
          action: site_facts
        - action: command echo {{ my_custom_fact_can_be_used_now }}

One useful trick with *when* is to key off the changed result of a last command.  As an example::

    tasks:
        - action: template src=/templates/foo.j2 dest=/etc/foo.conf
          register: last_result
        - action: command echo 'the file has changed'
          when: last_result.changed

{{ last_result }} is a variable set by the register directive. This assumes Ansible 0.8 and later.

When combining `when` with `with_items`, be aware that the `when` statement is processed separately for each item.
This is by design::

    tasks:
        - action: command echo {{ item }}
          with_items: [ 0, 2, 4, 6, 8, 10 ]
          when: item > 5

Note that if you have several tasks that all share the same conditional statement, you can affix the conditional
to a task include statement as below.  Note this does not work with playbook includes, just task includes.  All the tasks
get evaluated, but the conditional is applied to each and every task::

    - include: tasks/sometasks.yml
      when: "'reticulating splines' in output"

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
        - [ "vars/{{ ansible_os_family }}.yml", "vars/os_defaults.yml" ]
      tasks:
      - name: make sure apache is running
        action: service name={{ apache }} state=running

.. note::
   The variable 'ansible_os_family' is being interpolated into
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

    - name: add several users
      action: user name={{ item }} state=present groups=wheel
      with_items:
         - testuser1
         - testuser2

If you have defined a YAML list in a variables file, or the 'vars' section, you can also do::

    with_items: somelist

The above would be the equivalent of::

    - name: add user testuser1
      action: user name=testuser1 state=present groups=wheel
    - name: add user testuser2
      action: user name=testuser2 state=present groups=wheel

The yum and apt modules use with_items to execute fewer package manager transactions.

Note that the types of items you iterate over with 'with_items' do not have to be simple lists of strings.
If you have a list of hashes, you can reference subkeys using things like::

    - name: add several users
      action: user name={{ item.name }} state=present groups={{ item.groups }}
      with_items:
        - { name: 'testuser1', groups: 'wheel' }
        - { name: 'testuser2', groups: 'root' }

Lookup Plugins - Accessing Outside Data
```````````````````````````````````````

.. versionadded: 0.8

Various *lookup plugins* allow additional ways to iterate over data.  Ansible will have more of these
over time.  You can write your own, as is covered in the API section.  Each typically takes a list and
can accept more than one parameter.

``with_fileglob`` matches all files in a single directory, non-recursively, that match a pattern.  It can
be used like this::

    ---
    - hosts: all

      tasks:

        # first ensure our target directory exists
        - action: file dest=/etc/fooapp state=directory

        # copy each file over that matches the given pattern
        - action: copy src={{ item }} dest=/etc/fooapp/ owner=root mode=600
          with_fileglob:
            - /playbooks/files/fooapp/*

``with_file`` loads data in from a file directly::

        - action: authorized_key user=foo key={{ item }}
          with_file:
             - /home/foo/.ssh/id_rsa.pub

.. note::

   When using ``with_fileglob`` or ``with_file`` with :ref:`roles`, if you
   specify a relative path (e.g., :file:`./foo`), Ansible resolves the path
   relative to the :file:`roles/<rolename>/files` directory.

.. versionadded: 0.9

Many new lookup abilities were added in 0.9.  Remeber lookup plugins are run on the *controlling* machine::

    ---
    - hosts: all

      tasks:

         - action: debug msg="{{ lookup('env','HOME') }} is an environment variable"

         - action: debug msg="{{ item }} is a line from the result of this command"
           with_lines:
             - cat /etc/motd

         - action: debug msg="{{ lookup('pipe','date') }} is the raw result of running this command"

         - action: debug msg="{{ lookup('redis_kv', 'redis://localhost:6379,somekey') }} is value in Redis for somekey"

         - action: debug msg="{{ lookup('dnstxt', 'example.com') }} is a DNS TXT record for example.com"

         - action: debug msg="{{ lookup('template', './some_template.j2') }} is a value from evaluation of this template"

As an alternative you can also assign lookup plugins to variables or use them
elsewhere.  This macros are evaluated each time they are used in a task (or
template)::

    vars:
      motd_value: "{{ lookup('file', '/etc/motd') }}"

    tasks:
      - debug: msg="motd value is {{ motd_value }}"

.. versionadded: 1.0

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

.. versionadded: 1.1

``with_password`` and associated lookup macro generate a random plaintext password and store it in
a file at a given filepath.  Support for crypted save modes (as with vars_prompt) are pending.  If the
file exists previously, it will retrieve its contents, behaving just like with_file. Usage of variables like "{{ inventory_hostname }}" in the filepath can be used to set
up random passwords per host (what simplifies password management in 'host_vars' variables).

Generated passwords contain a random mix of upper and lowercase ASCII letters, the
numbers 0-9 and punctuation (". , : - _"). The default length of a generated password is 30 characters.
This length can be changed by passing an extra parameter::

    ---
    - hosts: all

      tasks:

        # create a mysql user with a random password:
        - mysql_user: name={{ client }}
                      password="{{ lookup('password', 'credentials/' + client + '/' + tier + '/' + role + '/mysqlpassword length=15') }}"
                      priv={{ client }}_{{ tier }}_{{ role }}.*:ALL

        (...)

        # dump a mysql database with a given password (this example showing the other form).
        - mysql_db: name={{ client }}_{{ tier }}_{{ role }}
                    login_user={{ client }}
                    login_password={{ item }}
                    state=dump
                    target=/tmp/{{ client }}_{{ tier }}_{{ role }}_backup.sql
          with_password: credentials/{{ client }}/{{ tier }}/{{ role }}/mysqlpassword length=15

        (...)

        # create an user with a given password
        - user: name=guestuser
                state=present
                uid=5000
                password={{ item }}
          with_password: credentials/{{ hostname }}/userpassword encrypt=sha256_crypt

Setting the Environment (and Working With Proxies)
``````````````````````````````````````````````````

.. versionadded: 1.1

It is quite possible that you may need to get package updates through a proxy, or even get some package
updates through a proxy and access other packages not through a proxy.  Ansible makes it easy for you
to configure your environment by using the 'environment' keyword.  Here is an example::

    - hosts: all
      user: root

      tasks:

        - apt: name=cobbler state=installed
          environment:
            http_proxy: http://proxy.example.com:8080

The environment can also be stored in a variable, and accessed like so::

    - hosts: all
      user: root

      # here we make a variable named "env" that is a dictionary
      vars:
        proxy_env:
          http_proxy: http://proxy.example.com:8080

      tasks:

        - apt: name=cobbler state=installed
          environment: "{{ proxy_env }}"

While just proxy settings were shown above, any number of settings can be supplied.  The most logical place
to define an environment hash might be a group_vars file, like so::

    ---
    # file: group_vars/boston

    ntp_server: ntp.bos.example.com
    backup: bak.bos.example.com
    proxy_env:
      http_proxy: http://proxy.bos.example.com:8080
      https_proxy: http://proxy.bos.example.com:8080

Getting values from files
`````````````````````````

.. versionadded:: 0.8

Sometimes you'll want to include the content of a file directly into a playbook.  You can do so using a macro.
This syntax will remain in future versions, though we will also will provide ways to do this via lookup plugins (see "More Loops") as well.  What follows
is an example using the authorized_key module, which requires the actual text of the SSH key as a parameter::

    tasks:
        - name: enable key-based ssh access for users
          authorized_key: user={{ item }} key="{{ lookup('file', '/keys/' + item ) }}"
          with_items:
             - pinky
             - brain
             - snowball

Selecting Files And Templates Based On Variables
````````````````````````````````````````````````

Sometimes a configuration file you want to copy, or a template you will use may depend on a variable.
The following construct selects the first available file appropriate for the variables of a given host, which is often much cleaner than putting a lot of if conditionals in a template.

The following example shows how to template out a configuration file that was very different between, say, CentOS and Debian::

    - name: template a file
      action: template src={{ item }} dest=/etc/myapp/foo.conf
      first_available_file:
        - /srv/templates/myapp/{{ ansible_distribution }}.conf
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

The 'register' keyword decides what variable to save a result in.  The resulting variables can be used in templates, action lines, or *when* statements.  It looks like this (in an obviously trivial example)::

    - name: test play
      hosts: all

      tasks:

          - action: shell cat /etc/motd
            register: motd_contents

          - action: shell echo "motd contains the word hi"
            when: motd_contents.stdout.find('hi') != -1


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
        action: command /usr/bin/take_out_of_pool {{ inventory_hostname }}
        delegate_to: 127.0.0.1

      - name: actual steps would go here
        action: yum name=acme-web-stack state=latest

      - name: add back to load balancer pool
        action: command /usr/bin/add_back_to_pool {{ inventory_hostname }}
        delegate_to: 127.0.0.1


These commands will run on 127.0.0.1, which is the machine running Ansible. There is also a shorthand syntax that
you can use on a per-task basis: 'local_action'. Here is the same playbook as above, but using the shorthand
syntax for delegating to 127.0.0.1::

    ---
    # ...
      tasks:
      - name: take out of load balancer pool
        local_action: command /usr/bin/take_out_of_pool {{ inventory_hostname }}

    # ...

      - name: add back to load balancer pool
        local_action: command /usr/bin/add_back_to_pool {{ inventory_hostname }}

A common pattern is to use a local action to call 'rsync' to recursively copy files to the managed servers.
Here is an example::

    ---
    # ...
      tasks:
      - name: recursively copy files from management server to target
        local_action: command rsync -a /path/to/files {{ inventory_hostname }}:/path/to/target/

Note that you must have passphrase-less SSH keys or an ssh-agent configured for this to work, otherwise rsync
will need to ask for a passphrase.

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
          - action: shell echo "Hello {{ item }}"
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
          - action: pip name={{ item }} state=present
            with_items:
              - pyzmq
              - pyasn1
              - PyCrypto
              - python-keyczar

Fedora and EPEL also have Ansible RPM subpackages available for fireball-dependencies.

Also see the module documentation section.


Understanding Variable Precedence
`````````````````````````````````

You have already learned about inventory variables, 'vars', and 'vars_files'.  In the
event the same variable name occurs in more than one place, what happens?  There are really three tiers
of precedence, and within those tiers, some minor ordering rules that you probably won't even need to remember.
We'll explain them anyway though.

Variables that are set during the execution of the play have highest priority. This includes registered
variables and facts, which are discovered pieces of information about remote hosts.

Descending in priority are variables defined in the playbook.  'vars_files' as defined in the playbook are next up,
followed by variables as passed to ansible-playbook via --extra-vars (-e), then variables defined in the 'vars' section.  These
should all be taken to be basically the same thing -- good places to define constants about what the play does to all hosts
in the play.

Finally, inventory variables have the least priority.  Variables about hosts override those about groups.
If a variable is defined in multiple groups and one group is a child of the other, the child group variable
will override the variable set in the parent.

This makes the 'group_vars/all' file the best place to define a default value you wish to override in another
group, or even in a playbook.  For example, your organization might set a default ntp server in group_vars/all
and then override it based on a group based on a geographic region.  However if you type 'ntpserver: asdf.example.com'
in a vars section of a playbook, you know from reading the playbook that THAT specific value is definitely the one
that is going to be used.  You won't be fooled by some variable from inventory sneaking up on you.

So, in short, if you want something easy to remember: facts beat playbook definitions, and
playbook definitions beat inventory variables.


Check Mode ("Dry Run") --check
```````````````````````````````

.. versionadded:: 1.1

When ansible-playbook is executed with --check it will not make any changes on remote systems.  Instead, any module
instrumented to support 'check mode' (which contains the primary core modules, but it is not required that all modules do
this) will report what changes they would have made.  Other modules that do not support check mode will also take no
action, but just will not report what changes they might have made.

Check mode is just a simulation, and if you have steps that use conditionals that depend on the results of prior commands,
it may be less useful for you.  However it is great for one-node-at-time basic configuration management use cases.

Example::

    ansible-playbook foo.yml --check

Showing Differences with --diff
```````````````````````````````

.. versionadded:: 1.1

The --diff option to ansible-playbook works great with --check (detailed above) but can also be used by itself.  When this flag is supplied, if any templated files on the remote system are changed, and the ansible-playbook CLI will report back
the textual changes made to the file (or, if used with --check, the changes that would have been made).  Since the diff
feature produces a large amount of output, it is best used when checking a single host at a time, like so::

    ansible-playbook foo.yml --check --diff --limit foo.example.com

Dictionary & Nested (Complex) Arguments
```````````````````````````````````````

As a review, most tasks in ansible are of this form::

    tasks:

      - name: ensure the cobbler package is installed
        yum: name=cobbler state=installed

However, in some cases, it may be useful to feed arguments directly in from a hash (dictionary).  In fact, a very small
number of modules (the CloudFormations module is one) actually require complex arguments.  They work like this::

    tasks:

      - name: call a module that requires some complex arguments
        foo_module:
           fibonacci_list:
             - 1
             - 1
             - 2
             - 3
           my_pets:
             dogs:
               - fido
               - woof
             fish:
               - limpet
               - nemo
               - "{{ other_fish_name }}"

You can of course use variables inside these, as noted above.

If using local_action, you can do this::

    - name: call a module that requires some complex arguments
      local_action:
        module: foo_module
        arg1: 1234
        arg2: 'asdf'

Which of course means, though more verbose, this is also technically legal syntax::

    - name: foo
      template: { src: '/templates/motd.j2', dest: '/etc/motd' }

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


