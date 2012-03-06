Ansible
=======

Ansible is a extra-simple tool/API for doing 'parallel remote things' over SSH -- whether
executing commands, running "modules", or executing larger 'playbooks' that 
can serve as a configuration management or deployment system.

While [Func](http://fedorahosted.org/func), which I co-wrote, 
aspired to avoid using SSH and have it's own daemon infrastructure, 
Ansible aspires to be quite different and more minimal, but still able 
to grow more modularly over time.  This is based on talking to a lot of 
users of various tools and wishing to eliminate problems with connectivity 
and long running daemons, or not picking tool X because they preferred to 
code in Y. Further, playbooks take things a whole step further, building the config
and deployment system I always wanted to build.

Why use Ansible versus something else?  (Fabric, Capistrano, mCollective, 
Func, SaltStack, etc?) It will have far less code, it will be more correct, 
and it will be the easiest thing to hack on and use you'll ever see -- 
regardless of your favorite language of choice.  Want to only code plugins 
in bash or clojure?  Ansible doesn't care.  The docs will fit on one page 
and the source will be blindingly obvious.

Design Principles
=================

   * Dead simple setup
   * Super fast & parallel by default
   * No server or client daemons; use existing SSHd
   * No additional software required on client boxes
   * Modules can be written in ANY language
   * Awesome API for creating very powerful distributed scripts
   * Be usable as non-root
   * Create the easiest config management system to use, ever.

Requirements
============

Requirements are extremely minimal.

If you are running python 2.6 on the 'overlord' machine, you will need:

   * paramiko
   * python-jinja2
   * PyYAML (if using playbooks)

If you are running less than Python 2.6, you will also need

   * the Python 2.4 or 2.5 backport of the multiprocessing module
   * simplejson

On the managed nodes, to use templating, you will need:

   * python-jinja2 (you can install this with ansible)

Patterns and Groups
===================

Ansible works off an inventory file (/etc/ansible/hosts or overrideable with -i).  Hosts can
be listed by IP or hostname, and groups are denoted with square brackets:

Example:

    abc.example.com
    def.example.com

    [atlanta]
    192.168.10.50
    192.168.10.51
   
    [raleigh]
    192.168.10.52

When running ansible commands, hosts are addressed by name, wildcard, or group name. 
This specifier is used in all ansible commands.  'all' is a built-in group name that matches all
hosts.  Group names and host wildcards can be mixed as needed:

    all
    'web*.example.com'
    'appservers;dbservers'
    'atlanta;raleigh'
    '192.168.10.50'

Example: Massive Parallelism and Running Shell Commands
=======================================================

Reboot all web servers in Atlanta, 10 at a time:
 
    > ssh-agent bash
    > ssh-add ~/.ssh/id_rsa.pub

    > ansible atlanta -a "/sbin/reboot" -f 10

The -f 10 specifies the usage of 10 simultaneous processes.

Note that other than the command module, ansible modules do not work like simple scripts.  They make
the remote system look like you state, and run the commands neccessary to get it there.

Example: Time-limited Background Operations
===========================================

Long running operations can be backgrounded, and their status can be checked on later.  The same
job ID is given to the same task on all hosts, so you won't lose track.  Polling support
is pending in the command line.

    > ansible all -B 3600 -a "/usr/bin/long_running_operation --do-stuff"
    > ansible all -n job_status -a jid=123456789

Any module other than 'copy' or 'template' can be backgrounded.

Example: File Transfer and Templating
=====================================

Ansible can SCP lots of files to multiple machines in parallel, and optionally use
them as template sources.

To just transfer a file directly to many different servers:

    > ansible atlanta copy -a "/etc/hosts /tmp/hosts"

To use templating, first run the setup module to put the template variables you would
like to use on the remote host.  Then use the template module to write the
files using the templates.  Templates are written in Jinja2 format.

    > ansible webservers -m setup    -a "favcolor=red ntp_server=192.168.1.1"
    > ansible webservers -m template -a "src=/srv/motd.j2 dest=/etc/motd"
    > ansible webservers -m template -a "src=/srv/ntp.j2 dest=/etc/ntp.conf"

Need something like the fqdn in a template?  If facter or ohai are installed, data from these projects
will also be made available to the template engine, using 'facter_' and 'ohai_' prefixes for each.

Example: Software Deployment From Source Control
================================================

Deploy your webapp straight from git

    > ansible webservers -m git -a "repo=git://foo dest=/srv/myapp version=HEAD"

Since ansible modules can notify change handlers (see 'Playbooks') it is possible
to tell ansible to run specific tasks when the code is updated, such as deploying
Perl/Python/PHP/Ruby directly from git and then restarting apache.


Other Modules
=============

Ansible has lots of other modules and they are growing.

See the library directory in the source checkout or the manpage:
[ansible-modules(5)](https://github.com/mpdehaan/ansible/blob/master/docs/man/man5/ansible-modules.5.asciidoc) that covers what's there and all the options they take.

Playbooks
=========

Playbooks are a completely different way to use ansible and are particularly awesome.

They are the basis for a really simple configuration management system, unlike
any that already exist, and one that is very well suited to deploying complex
multi-machine applications.  

An example showing a small playbook:

    ---
    - hosts: all
      vars:
        http_port: 80
        max_clients: 200
      user: root
      tasks:
      - include: base.yml
      - name: configure template & module variables for future template calls
        action: setup http_port=80 max_clients=200
      - name: write the apache config file
        action: template src=/srv/httpd.j2 dest=/etc/httpd.conf
        notify:
        - restart apache
      - name: ensure apache is running
        action: service name=httpd state=started
      handlers:
        - include: handlers.yml

Some key concepts here include:

   * Everything is expressed in simple YAML
   * Steps can be run as non-root
   * Modules can notify 'handlers' when changes occur.
   * Tasks and handlers can be 'included' to faciliate sharing and 'class' like behavior

To run a playbook:

    ansible-playbook playbook.yml

See the playbook format manpage -- [ansible-playbook(5)](https://github.com/mpdehaan/ansible/blob/master/docs/man/man5/ansible-playbook.5.asciidoc) for more details.


API
===

The Python API is very powerful, and is how the ansible CLI and ansible-playbook
are implemented.

    import ansible.runner

    runner = ansible.runner.Runner(
       module_name='ping',
       module_args='',
       pattern='web*',
       forks=10
    )
    datastructure = runner.run()

The run method returns results per host, grouped by whether they 
could be contacted or not.  Return types are module specific, as
expressed in the 'ansible-modules' manpage.

    {
        "dark" : {
           "web1.example.com" : "failure message"
        }
        "contacted" : {
           "web2.example.com" : 1
        }
    }

A module can return any type of JSON data it wants, so Ansible can
be used as a framework to rapidly build powerful applications and scripts.

License
=======

GPLv3

Communicate
===========

   * [ansible-project mailing list](http://groups.google.com/group/ansible-project)
   * irc.freenode.net: #ansible

Author
======

Michael DeHaan -- michael.dehaan@gmail.com

[http://michaeldehaan.net](http://michaeldehaan.net/)


