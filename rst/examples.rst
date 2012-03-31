Command Line Examples
=====================

The following examples show how to use `/usr/bin/ansible` for running ad-hoc tasks.
Start here.  For configuration management and deployments, you'll want to pick up on
using `/usr/bin/ansible-playbook` -- the concepts port over directly.


Parallelism and Shell Commands
``````````````````````````````

Let's use ansible's command line tool to reboot all web servers in Atlanta, 10 at a time::

    ssh-agent bash
    ssh-add ~/.ssh/id_rsa.pub

    ansible atlanta -a "/sbin/reboot" -f 10

The -f 10 specifies the usage of 10 simultaneous processes.

.. note::

   Note that other than the :ref:`command` module, ansible modules do
   not work like simple scripts. They make the remote system look like
   you state, and run the commands necessary to get it there.  This
   is commonly referred to as 'idempotent'.

File Transfer & Templating
``````````````````````````

Ansible can SCP lots of files to multiple machines in parallel, and
optionally use them as template sources.

To just transfer a file directly to many different servers::

    ansible atlanta -m copy -a "/etc/hosts /tmp/hosts"

To use templating, first run the setup module to put the template
variables you would like to use on the remote host. Then use the
template module to write the files using those templates. 

Templates are written in Jinja2 format. Playbooks (covered elsewhere in the
documentation) will run the setup module for you, making this even
simpler::

    ansible webservers -m setup    -a "favcolor=red ntp_server=192.168.1.1"
    ansible webservers -m template -a "src=/srv/motd.j2 dest=/etc/motd"
    ansible webservers -m template -a "src=/srv/ntp.j2 dest=/etc/ntp.conf"

Ansible variables are used in templates by using the name surrounded by double
curly-braces.  If facter or ohai were installed on the remote machine, variables
from those programs can be accessed too, which the appropriate prefix::

    This is an Ansible variable: {{ favcolor }}
    This is a facter variable: {{ facter_hostname }}
    This is an ohai variable: {{ ohai_foo }}

The `file` module allows changing ownership and permissions on files.  These
same options can be passed directly to the `copy` or `template` modules as well::

    ansible webservers -m file -a "dest=/srv/foo/a.txt mode=600"
    ansible webservers -m file -a "dest=/srv/foo/b.txt mode=600 owner=mdehaan group=mdehaan"

The `file` module can also create directories, similar to `mkdir -p`::
    
    ansible webservers -m file -a "dest=/path/to/c mode=644 owner=mdehaan group=mdehaan state=directory"

As well as delete directories (recursively) and delete files::
    
    ansible webservers -m file -a "dest=/path/to/c state=absent"

The mode, owner, and group flags can also be used on the copy or template lines.


Managing Packages
`````````````````

Ensure a package is installed, but don't update it::
    
    ansible webservers -m yum -a "pkg=acme state=installed"

Ensure a package is installed to a specific version::

    ansible-webservers -m yum -a "pkg=acme-1.5 state=installed"

Ensure a package is at the latest version::

    ansible webservers -m yum -a "pkg=acme state=latest" 

Ensure a package is not installed:
    
    ansible-webservers -m yum -a "pkg=acme state=removed"

Currently Ansible only has a module for managing packages with yum.  You can install
for other package manages using the command module or contribute a module
for other package managers.  Stop by the mailing list for info/details.

Deploying From Source Control
`````````````````````````````

Deploy your webapp straight from git::

    ansible webservers -m git -a "repo=git://foo dest=/srv/myapp version=HEAD"

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

Any module other than :ref:`copy` or :ref:`template` can be
backgrounded.  Typically you'll be backgrounding long-running 
shell commands or software upgrades only.

.. seealso::

   :doc:`modules`
       A list of available modules
   :doc:`playbooks`
       Using ansible for configuration management & deployment


