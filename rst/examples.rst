Command Line Examples
=====================

The following examples show how to use `/usr/bin/ansible` for running ad-hoc tasks.
Start here.  For configuration management and deployments, you'll want to pick up on
using `/usr/bin/ansible-playbook` -- the concepts port over directly.

.. seealso::

   :doc:`modules`
       A list of available modules
   :doc:`playbooks`
       Alternative ways to use ansible


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
template module to write the files using the templates. Templates are
written in Jinja2 format. Playbooks (covered elsewhere in the
documentation) will run the setup module for you, making this even
simpler.::

    ansible webservers -m setup    -a "favcolor=red ntp_server=192.168.1.1"
    ansible webservers -m template -a "src=/srv/motd.j2 dest=/etc/motd"
    ansible webservers -m template -a "src=/srv/ntp.j2 dest=/etc/ntp.conf"

Need something like the fqdn in a template? If facter or ohai are
installed, data from these projects will also be made available to the
template engine, using 'facter' and 'ohai' prefixes for each.

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

  


