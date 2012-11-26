Command Line Examples And Next Steps
====================================

.. highlight:: bash

The following examples show how to use `/usr/bin/ansible` for running
ad hoc tasks.  Start here.

For configuration management and deployments, you'll want to pick up on
using `/usr/bin/ansible-playbook` -- the concepts port over directly.
(See :doc:`playbooks` for more information about those)

.. contents::
   :depth: 2
   :backlinks: top


Parallelism and Shell Commands
``````````````````````````````

Let's use ansible's command line tool to reboot all web servers in Atlanta, 10 at a time.  First, let's
set up SSH-agent so it can remember our credentials::

    $ ssh-agent bash
    $ ssh-add ~/.ssh/id_rsa.pub

If you don't want to use ssh-agent and want to instead SSH with a
password instead of keys, you can with ``--ask-pass`` (``-k``), but
it's much better to just use ssh-agent.

Now to run the command on all servers in a group, in this case,
*atlanta*, in 10 parallel forks::

    $ ansible atlanta -a "/sbin/reboot" -f 10

In 0.7 and later, this will default to running from your user account.  If you do not like this
behavior, pass in "-u username".  (In 0.6 and before, it defaulted to root.  Most folks prefered
defaulting to the current user, so we changed it).

If you want to run commands as a different user, it looks like this::

    $ ansible atlanta -a "/usr/bin/foo" -u username

If you want to run commands through sudo::

    $ ansible atlanta -a "/usr/bin/foo" -u username --sudo [--ask-sudo-pass]

Use ``--ask-sudo-pass`` (``-K``) if you are not using passwordless
sudo.  This will interactively prompt you for the password to use.
Use of passwordless sudo makes things easier to automate, but it's not
required.

It is also possible to sudo to a user other than root using
``--sudo-user`` (``-U``)::

    $ ansible atlanta -a "/usr/bin/foo" -u username -U otheruser [--ask-sudo-pass]

Ok, so those are basics.  If you didn't read about patterns and groups yet, go back and read :doc:`patterns`.

The ``-f 10`` in the above specifies the usage of 10 simultaneous
processes.  Normally commands also take a ``-m`` for module name, but
the default module name is 'command', so we didn't need to
specify that all of the time.  We'll use ``-m`` in later examples to
run some other :doc:`modules`.

.. note::
   The :ref:`command` module requires absolute paths and does not
   support shell variables.  If we want to execute a module using a
   shell, we can do those things, and also use pipe and redirection
   operators.  Read more about the differences on the :doc:`modules`
   page.

Using the :ref:`shell` module looks like this::

    $ ansible raleigh -m shell -a 'echo $TERM'

When running any command with the ansible *ad hoc* CLI (as opposed to
:doc:`playbooks`), pay particular attention to shell quoting rules, so
the shell doesn't eat a variable before it gets passed to Ansible.
For example, using double vs single quotes in the above example would
evaluate the variable on the box you were on.

So far we've been demoing simple command execution, but most Ansible modules usually do not work like
simple scripts. They make the remote system look like you state, and run the commands necessary to
get it there.  This is commonly referred to as 'idempotence', and is a core design goal of ansible.
However, we also recognize that running *ad hoc* commands is equally important, so Ansible easily supports both.


File Transfer
`````````````

Here's another use case for the `/usr/bin/ansible` command line.  Ansible can SCP lots of files to multiple machines in parallel.

To transfer a file directly to many different servers::

    $ ansible atlanta -m copy -a "src=/etc/hosts dest=/tmp/hosts"

If you use playbooks, you can also take advantage of the ``template`` module,
which takes this another step further.  (See module and playbook documentation).

The ``file`` module allows changing ownership and permissions on files.  These
same options can be passed directly to the ``copy`` module as well::

    $ ansible webservers -m file -a "dest=/srv/foo/a.txt mode=600"
    $ ansible webservers -m file -a "dest=/srv/foo/b.txt mode=600 owner=mdehaan group=mdehaan"

The ``file`` module can also create directories, similar to ``mkdir -p``::

    $ ansible webservers -m file -a "dest=/path/to/c mode=644 owner=mdehaan group=mdehaan state=directory"

As well as delete directories (recursively) and delete files::

    $ ansible webservers -m file -a "dest=/path/to/c state=absent"


Managing Packages
`````````````````

There are modules available for yum and apt.  Here are some examples
with yum.

Ensure a package is installed, but don't update it::

    $ ansible webservers -m yum -a "pkg=acme state=installed"

Ensure a package is installed to a specific version::

    $ ansible webservers -m yum -a "pkg=acme-1.5 state=installed"

Ensure a package is at the latest version::

    $ ansible webservers -m yum -a "pkg=acme state=latest"

Ensure a package is not installed::

    $ ansible webservers -m yum -a "pkg=acme state=removed"

Currently Ansible only has modules for managing packages with yum and apt.  You can install
for other packages for now using the command module or (better!) contribute a module
for other package managers.  Stop by the mailing list for info/details.

Users and Groups
````````````````

The 'user' module allows easy creation and manipulation of
existing user accounts, as well as removal of user accounts that may
exist::

    $ ansible all -m user -a "name=foo password=<crypted password here>"

    $ ansible all -m user -a "name=foo state=absent"

See the :doc:`modules` section for details on all of the available options, including
how to manipulate groups and group membership.

Deploying From Source Control
`````````````````````````````

Deploy your webapp straight from git::

    $ ansible webservers -m git -a "repo=git://foo.example.org/repo.git dest=/srv/myapp version=HEAD"

Since ansible modules can notify change handlers it is possible to
tell ansible to run specific tasks when the code is updated, such as
deploying Perl/Python/PHP/Ruby directly from git and then restarting
apache.

Managing Services
`````````````````

Ensure a service is started on all webservers::

    $ ansible webservers -m service -a "name=httpd state=started"

Alternatively, restart a service on all webservers::

    $ ansible webservers -m service -a "name=httpd state=restarted"

Ensure a service is stopped::

    $ ansible webservers -m service -a "name=httpd state=stopped"

Time Limited Background Operations
``````````````````````````````````

Long running operations can be backgrounded, and their status can be
checked on later. The same job ID is given to the same task on all
hosts, so you won't lose track.  If you kick hosts and don't want
to poll, it looks like this::

    $ ansible all -B 3600 -a "/usr/bin/long_running_operation --do-stuff"

If you do decide you want to check on the job status later, you can::

    $ ansible all -m async_status -a "jid=123456789"

Polling is built-in and looks like this::

    $ ansible all -B 1800 -P 60 -a "/usr/bin/long_running_operation --do-stuff"

The above example says "run for 30 minutes max (``-B``: 30*60=1800),
poll for status (``-P``) every 60 seconds".

Poll mode is smart so all jobs will be started before polling will begin on any machine.
Be sure to use a high enough ``--forks`` value if you want to get all of your jobs started
very quickly. After the time limit (in seconds) runs out (``-B``), the process on
the remote nodes will be terminated.

Typically you'll be only be backgrounding long-running
shell commands or software upgrades only.  Backgrounding the copy module does not do a background file transfer.  :doc:`playbooks` also support polling, and have a simplified syntax for this.

Limiting Selected Hosts
```````````````````````

.. versionadded:: 0.7

What hosts you select to manage can be additionally constrained by using the '--limit' parameter or
by using 'batch' (or 'range') selectors.

As mentioned above, patterns can be strung together to select hosts in more than one group::

    $ ansible webservers:dbservers -m command -a "/bin/foo xyz"

This is an "or" condition.  If you want to further constrain the selection, use --limit, which
also works with ``ansible-playbook``::

    $ ansible webservers:dbservers -m command -a "/bin/foo xyz" --limit region

Assuming version 0.9 or later, as with other host patterns, values to limit can be seperated with ";", ":", or ",".

Now let's talk about range selection.   Suppose you have 1000 servers in group 'datacenter', but only want to target one at a time.  This is also easy::

    $ ansible webservers[0-99] -m command -a "/bin/foo xyz"
    $ ansible webservers[100-199] -m command -a "/bin/foo xyz"

This will select the first 100, then the second 100, host entries in the webservers group.  (It does not matter
what their names or IP addresses are).

Both of these methods can be used at the same time, and ranges can also be passed to the --limit parameter.

Configuration & Defaults
````````````````````````

.. versionadded:: 0.7

Ansible has an optional configuration file that can be used to tune settings and also eliminate the need to pass various command line flags. Ansible will look for the config file in the following order, using
the first config file it finds present:

1. File specified by the ``ANSIBLE_CONFIG`` environment variable
2. ``ansible.cfg`` in the current working directory. (version 0.8 and up)
3. ``~/.ansible.cfg``
4. ``/etc/ansible/ansible.cfg``

For those running from source, a sample configuration file lives in the examples/ directory.  The RPM will install configuration into /etc/ansible/ansible.cfg automatically.

.. seealso::

   :doc:`modules`
       A list of available modules
   :doc:`playbooks`
       Using ansible for configuration management & deployment
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
