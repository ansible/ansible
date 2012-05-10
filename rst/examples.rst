Command Line Examples
=====================

The following examples show how to use `/usr/bin/ansible` for running ad-hoc tasks.
Start here. 

For configuration management and deployments, you'll want to pick up on
using `/usr/bin/ansible-playbook` -- the concepts port over directly.
(See :doc:`playbooks` for more information about those)

Parallelism and Shell Commands
``````````````````````````````

Let's use ansible's command line tool to reboot all web servers in Atlanta, 10 at a time.  First, let's
set up SSH-agent so it can remember our credentials::

    ssh-agent bash
    ssh-add ~/.ssh/id_rsa.pub

If you don't want to use ssh-agent and want to instead SSH with a password instead of keys, you can with
--ask-pass (-k), but it's much better to just use ssh-agent.

Now to run the command on all servers in a group, in this case, 'atlanta', in 10 parallel forks::

    ansible atlanta -a "/sbin/reboot" -f 10

If you want to run commands as a different user than root, it looks like this::

    ansible atlanta -a "/usr/bin/foo" -u yourname

If you want to run commands through sudo::
    
    ansible atlanta -a "/usr/bin/foo" -u yourname --sudo [--ask-sudo-pass]

Use --ask-sudo-pass (-K) if you are not using passwordless sudo.  This will interactively prompt
you for the password to use.  Use of passwordless sudo makes things easier to automate, but it's
not required.

It is also possible to sudo to a user other than root using --sudo-user (-U)::

    ansible atlanta -a "/usr/bin/foo" -u yourname -U otheruser [--ask-sudo-pass]

Ok, so those are basics.  If you didn't read about patterns and groups yet, go back and read :doc:`patterns`.

The -f 10 in the above specifies the usage of 10 simultaneous processes.  Normally commands also take
a `-m` for module name, but the default module name is 'command', so we didn't need to specify that
all of the time.  We'll use `-m` in later examples to run some other :doc:`modules`.

Note that the command module requires absolute paths and does not support shell variables.  If we want to 
execute a module using the shell, we can do those things, and also use pipe and redirection operators.
Read more about the differences on the :doc:`modules` page.  The shell
module looks like this::

    ansible raleigh -m shell -a 'echo $TERM'

When running any command with the ansible "ad hoc" CLI (as opposed to playbooks), pay particular attention
to shell quoting rules, so the shell doesn't eat a variable before it gets passed to Ansible.  For example,
using double vs single quotes in the above example would evaluate the variable on the box you were on.

So far we've been demoing simple command execution, but most ansible modules usually do not work like 
simple scripts. They make the remote system look like you state, and run the commands necessary to 
get it there.  This is commonly referred to as 'idempotence', and is a core design goal of ansible.  
However, we also recognize that running ad-hoc commands is equally important, so Ansible easily supports both.


File Transfer & Templating
``````````````````````````

Here's another use case for the `/usr/bin/ansible` command line.

Ansible can SCP lots of files to multiple machines in parallel, and
optionally use them as template sources.

To transfer a file directly to many different servers::

    ansible atlanta -m copy -a "src=/etc/hosts dest=/tmp/hosts"

To use templating, first run the setup module to put the template
variables you would like to use on the remote host. Then use the
template module to write the files using those templates. 

Templates are written in `Jinja2 <http://jinja.pocoo.org/docs/>`_ format.
Playbooks (covered elsewhere in the
documentation) will run the setup module for you, making this even
simpler::

    ansible webservers -m setup    -a "favcolor=red ntp_server=192.168.1.1"
    ansible webservers -m template -a "src=/srv/motd.j2 dest=/etc/motd"
    ansible webservers -m template -a "src=/srv/ntp.j2 dest=/etc/ntp.conf"

Ansible variables are used in templates by using the name surrounded by double
curly-braces.  Ansible provides some 'facts' about the system being managed
automatically in playbooks or when the setup module is run manually.  If facter or ohai 
were installed on the remote machine, variables
from those programs can be accessed too, using the appropriate prefix::

    This is an Ansible variable: {{ favcolor }}
    This is an Ansible fact: {{ ansible_hostname }}
    This is a facter fact: {{ facter_hostname }}
    This is an ohai fact: {{ ohai_foo }}

Using the Ansible facts is generally preferred as that way you can avoid a dependency
on ruby.  If you want to use facter instead, you will also need rubygem-json because
the facter packages may forget this as a dependency.

The `file` module allows changing ownership and permissions on files.  These
same options can be passed directly to the `copy` or `template` modules as well::

    ansible webservers -m file -a "dest=/srv/foo/a.txt mode=600"
    ansible webservers -m file -a "dest=/srv/foo/b.txt mode=600 owner=mdehaan group=mdehaan"

The `file` module can also create directories, similar to `mkdir -p`::
    
    ansible webservers -m file -a "dest=/path/to/c mode=644 owner=mdehaan group=mdehaan state=directory"

As well as delete directories (recursively) and delete files::
    
    ansible webservers -m file -a "dest=/path/to/c state=absent"

The mode, owner, and group arguments can also be used on the copy or template lines.


Managing Packages
`````````````````

There are modules available for yum and apt.  Here are some examples with yum.

Ensure a package is installed, but don't update it::
    
    ansible webservers -m yum -a "pkg=acme state=installed"

Ensure a package is installed to a specific version::

    ansible-webservers -m yum -a "pkg=acme-1.5 state=installed"

Ensure a package is at the latest version::

    ansible webservers -m yum -a "pkg=acme state=latest" 

Ensure a package is not installed::
 
    ansible-webservers -m yum -a "pkg=acme state=removed"

Currently Ansible only has modules for managing packages with yum and apt.  You can install
for other packages for now using the command module or (better!) contribute a module
for other package managers.  Stop by the mailing list for info/details.

Users and Groups
````````````````

The user module allows easy creation and manipulation of existing user accounts, as well
as removal of user accounts that may exist::

    ansible all -m user -a "name=foo password=<crypted password here>"

    ansible all -m user -a "name=foo state=absent"

See the :doc:`modules` section for details on all of the available options, including
how to manipulate groups and group membership.

Deploying From Source Control
`````````````````````````````

Deploy your webapp straight from git::

    ansible webservers -m git -a "repo=git://foo.example.org/repo.git dest=/srv/myapp version=HEAD"

Since ansible modules can notify change handlers (see
:doc:`playbooks`) it is possible to tell ansible to run specific tasks
when the code is updated, such as deploying Perl/Python/PHP/Ruby
directly from git and then restarting apache.

Managing Services
`````````````````

Ensure a service is started on all webservers::

    ansible webservers -m service -a "name=httpd state=started"

Alternatively, restart a service on all webservers::

    ansible webservers -m service -a "name=httpd state=restarted"

Ensure a service is stopped::

    ansible webservers -m service -a "name=httpd state=stopped"

Time Limited Background Operations
``````````````````````````````````

Long running operations can be backgrounded, and their status can be
checked on later. The same job ID is given to the same task on all
hosts, so you won't lose track.  If you kick hosts and don't want
to poll, it looks like this::

    ansible all -B 3600 -a "/usr/bin/long_running_operation --do-stuff"

If you do decide you want to check on the job status later, you can::

    ansible all -m async_status -a "jid=123456789"

Polling is built-in and looks like this::
    
    ansible all -B 3600 -P 60 -a "/usr/bin/long_running_operation --do-stuff"

The above example says "run for 60 minutes max (60*60=3600), poll for status every 60 seconds".

Poll mode is smart so all jobs will be started before polling will begin on any machine.
Be sure to use a high enough `--forks` value if you want to get all of your jobs started
very quickly. After the time limit (in seconds) runs out (``-B``), the process on
the remote nodes will be terminated.

Any module other than `copy` or `template` can be
backgrounded.  Typically you'll be backgrounding long-running 
shell commands or software upgrades only.  :doc:`playbooks` also support polling, and have
a simplified syntax for this.

.. seealso::

   :doc:`modules`
       A list of available modules
   :doc:`playbooks`
       Using ansible for configuration management & deployment
   `Mailing List <http://groups.google.com/group/ansible-project>`_ 
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel




