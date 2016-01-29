Introduction To Ad-Hoc Commands
===============================

.. contents:: Topics

.. highlight:: bash

The following examples show how to use `/usr/bin/ansible` for running
ad hoc tasks. 

What's an ad-hoc command?

An ad-hoc command is something that you might type in to do something really
quick, but don't want to save for later.

This is a good place to start to understand the basics of what Ansible can do
prior to learning the playbooks language -- ad-hoc commands can also be used
to do quick things that you might not necessarily want to write a full playbook for.

Generally speaking, the true power of Ansible lies in playbooks.
Why would you use ad-hoc tasks versus playbooks?

For instance, if you wanted to power off all of your lab for Christmas vacation,
you could execute a quick one-liner in Ansible without writing a playbook.

For configuration management and deployments, though, you'll want to pick up on
using '/usr/bin/ansible-playbook' -- the concepts you will learn here will
port over directly to the playbook language.

(See :doc:`playbooks` for more information about those)

If you haven't read :doc:`intro_inventory` already, please look that over a bit first
and then we'll get going.

.. _parallelism_and_shell_commands:

Parallelism and Shell Commands
``````````````````````````````

Arbitrary example.

Let's use Ansible's command line tool to reboot all web servers in Atlanta, 10 at a time.  First, let's
set up SSH-agent so it can remember our credentials::

    $ ssh-agent bash
    $ ssh-add ~/.ssh/id_rsa

If you don't want to use ssh-agent and want to instead SSH with a
password instead of keys, you can with ``--ask-pass`` (``-k``), but
it's much better to just use ssh-agent.

Now to run the command on all servers in a group, in this case,
*atlanta*, in 10 parallel forks::

    $ ansible atlanta -a "/sbin/reboot" -f 10

/usr/bin/ansible will default to running from your user account.  If you do not like this
behavior, pass in "-u username".  If you want to run commands as a different user, it looks like this::

    $ ansible atlanta -a "/usr/bin/foo" -u username

Often you'll not want to just do things from your user account.  If you want to run commands through privilege escalation::

    $ ansible atlanta -a "/usr/bin/foo" -u username --become [--ask-become-pass]

Use ``--ask-become-pass`` (``-K``) if you are not using a passwordless privilege escalation method (sudo/su/pfexec/doas/etc).
This will interactively prompt you for the password to use.
Use of a passwordless setup makes things easier to automate, but it's not required.

It is also possible to become a user other than root using
``--become-user``::

    $ ansible atlanta -a "/usr/bin/foo" -u username --become-user otheruser [--ask-become-pass]

.. note::

    Rarely, some users have security rules where they constrain their sudo/pbrun/doas environment to running specific command paths only.
    This does not work with ansible's no-bootstrapping philosophy and hundreds of different modules.
    If doing this, use Ansible from a special account that does not have this constraint.
    One way of doing this without sharing access to unauthorized users would be gating Ansible with :doc:`tower`, which
    can hold on to an SSH credential and let members of certain organizations use it on their behalf without having direct access.

Ok, so those are basics.  If you didn't read about patterns and groups yet, go back and read :doc:`intro_patterns`.

The ``-f 10`` in the above specifies the usage of 10 simultaneous
processes to use.   You can also set this in :doc:`intro_configuration` to avoid setting it again.  The default is actually 5, which
is really small and conservative.  You are probably going to want to talk to a lot more simultaneous hosts so feel free
to crank this up.  If you have more hosts than the value set for the fork count, Ansible will talk to them, but it will
take a little longer.  Feel free to push this value as high as your system can handle!

You can also select what Ansible "module" you want to run.  Normally commands also take a ``-m`` for module name, but
the default module name is 'command', so we didn't need to
specify that all of the time.  We'll use ``-m`` in later examples to
run some other :doc:`modules`.

.. note::
   The :ref:`command` module does not
   support shell variables and things like piping.  If we want to execute a module using a
   shell, use the 'shell' module instead. Read more about the differences on the :doc:`modules`
   page.

Using the :ref:`shell` module looks like this::

    $ ansible raleigh -m shell -a 'echo $TERM'

When running any command with the Ansible *ad hoc* CLI (as opposed to
:doc:`Playbooks <playbooks>`), pay particular attention to shell quoting rules, so
the local shell doesn't eat a variable before it gets passed to Ansible.
For example, using double rather than single quotes in the above example would
evaluate the variable on the box you were on.

So far we've been demoing simple command execution, but most Ansible modules usually do not work like
simple scripts. They make the remote system look like a state, and run the commands necessary to
get it there.  This is commonly referred to as 'idempotence', and is a core design goal of Ansible.
However, we also recognize that running arbitrary commands is equally important, so Ansible easily supports both.

.. _file_transfer:

File Transfer
`````````````

Here's another use case for the `/usr/bin/ansible` command line.  Ansible can SCP lots of files to multiple machines in parallel.

To transfer a file directly to many servers::

    $ ansible atlanta -m copy -a "src=/etc/hosts dest=/tmp/hosts"

If you use playbooks, you can also take advantage of the ``template`` module,
which takes this another step further.  (See module and playbook documentation).

The ``file`` module allows changing ownership and permissions on files.  These
same options can be passed directly to the ``copy`` module as well::

    $ ansible webservers -m file -a "dest=/srv/foo/a.txt mode=600"
    $ ansible webservers -m file -a "dest=/srv/foo/b.txt mode=600 owner=mdehaan group=mdehaan"

The ``file`` module can also create directories, similar to ``mkdir -p``::

    $ ansible webservers -m file -a "dest=/path/to/c mode=755 owner=mdehaan group=mdehaan state=directory"

As well as delete directories (recursively) and delete files::

    $ ansible webservers -m file -a "dest=/path/to/c state=absent"

.. _managing_packages:

Managing Packages
`````````````````

There are modules available for yum and apt.  Here are some examples
with yum.

Ensure a package is installed, but don't update it::

    $ ansible webservers -m yum -a "name=acme state=present"

Ensure a package is installed to a specific version::

    $ ansible webservers -m yum -a "name=acme-1.5 state=present"

Ensure a package is at the latest version::

    $ ansible webservers -m yum -a "name=acme state=latest"

Ensure a package is not installed::

    $ ansible webservers -m yum -a "name=acme state=absent"

Ansible has modules for managing packages under many platforms.  If your package manager
does not have a module available for it, you can install
packages using the command module or (better!) contribute a module
for other package managers.  Stop by the mailing list for info/details.

.. _users_and_groups:

Users and Groups
````````````````

The 'user' module allows easy creation and manipulation of
existing user accounts, as well as removal of user accounts that may
exist::

    $ ansible all -m user -a "name=foo password=<crypted password here>"

    $ ansible all -m user -a "name=foo state=absent"

See the :doc:`modules` section for details on all of the available options, including
how to manipulate groups and group membership.

.. _from_source_control:

Deploying From Source Control
`````````````````````````````

Deploy your webapp straight from git::

    $ ansible webservers -m git -a "repo=git://foo.example.org/repo.git dest=/srv/myapp version=HEAD"

Since Ansible modules can notify change handlers it is possible to
tell Ansible to run specific tasks when the code is updated, such as
deploying Perl/Python/PHP/Ruby directly from git and then restarting
apache.

.. _managing_services:

Managing Services
`````````````````

Ensure a service is started on all webservers::

    $ ansible webservers -m service -a "name=httpd state=started"

Alternatively, restart a service on all webservers::

    $ ansible webservers -m service -a "name=httpd state=restarted"

Ensure a service is stopped::

    $ ansible webservers -m service -a "name=httpd state=stopped"

.. _time_limited_background_operations:

Time Limited Background Operations
``````````````````````````````````

Long running operations can be backgrounded, and their status can be checked on
later. If you kick hosts and don't want to poll, it looks like this::

    $ ansible all -B 3600 -P 0 -a "/usr/bin/long_running_operation --do-stuff"

If you do decide you want to check on the job status later, you can use the
async_status module, passing it the job id that was returned when you ran
the original job in the background::

    $ ansible web1.example.com -m async_status -a "jid=488359678239.2844"

Polling is built-in and looks like this::

    $ ansible all -B 1800 -P 60 -a "/usr/bin/long_running_operation --do-stuff"

The above example says "run for 30 minutes max (``-B``: 30*60=1800),
poll for status (``-P``) every 60 seconds".

Poll mode is smart so all jobs will be started before polling will begin on any machine.
Be sure to use a high enough ``--forks`` value if you want to get all of your jobs started
very quickly. After the time limit (in seconds) runs out (``-B``), the process on
the remote nodes will be terminated.

Typically you'll only be backgrounding long-running
shell commands or software upgrades.  Backgrounding the copy module does not do a background file transfer.  :doc:`Playbooks <playbooks>` also support polling, and have a simplified syntax for this.

.. _checking_facts:

Gathering Facts
```````````````

Facts are described in the playbooks section and represent discovered variables about a
system.  These can be used to implement conditional execution of tasks but also just to get ad-hoc information about your system. You can see all facts via::

    $ ansible all -m setup

It's also possible to filter this output to just export certain facts, see the "setup" module documentation for details.

Read more about facts at :doc:`playbooks_variables` once you're ready to read up on :doc:`Playbooks <playbooks>`. 

.. seealso::

   :doc:`intro_configuration`
       All about the Ansible config file
   :doc:`modules`
       A list of available modules
   :doc:`playbooks`
       Using Ansible for configuration management & deployment
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
