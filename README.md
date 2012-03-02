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

For the server the tool is running from, *only*:

   * paramiko
   * python 2.6 (or the 2.4/2.5 backport of the multiprocessing module)
   * PyYAML (only if using playbooks)

Optional -- If you want to push templates, the nodes need a template library,
which for bonus points you can install with ansible!  Easy enough.

   * python-jinja2 

Patterns and Groups
===================

Ansible works off an inventory file (/etc/ansible/hosts or overrideable with -i).  Hosts can
be listed by IP or hostname, and groups are supported with square brackets:

Example:

    abc.example.com
    def.example.com

    [atlanta]
    192.168.10.50
    192.168.10.51
   
    [raleigh]
    192.168.10.52

When running ansible commands, specific hosts are addressed by wildcard or group name. 
The default pattern is '*', meaning all ansible hosts.

    -p '*.example.com'
    -p 'atlanta;raleigh'
    -p 'database*;appserver*'
    -p '192.168.10.50;192.168.10.52'

Example: Massive Parallelism and Running Shell Commands
=======================================================

Reboot all web servers in Atlanta, 10 at a time:
 
    ssh-agent bash
    ssh-add ~/.ssh/id_rsa.pub

    ansible -p "atlanta-web*" -f 10 -n command -a "/sbin/reboot"

The -f 10 specifies the usage of 10 simultaneous processes.

Note that other than the command module, ansible modules do not work like simple scripts.  They make
the remote system look like you state, and run the commands neccessary to get it there.

[Read the ansible manpage](https://github.com/mpdehaan/ansible/blob/master/docs/man/man1/ansible.1.asciidoc)

Example: File Transfer and Templating
=====================================

Ansible can SCP lots of files to multiple machines in parallel, and optionally use
them as template sources.

To just transfer a file directly to many different servers:

    ansible -n copy -a "/etc/hosts /tmp/hosts"

To use templating, first run the setup module to put the template variables you would
like to use on the remote host.  Then use the template module to write the
files using the templates.  Templates are written in Jinja2 format.

    ansible -p webservers -n setup -a "favcolor=red ntp_server=192.168.1.1"
    ansible -p webservers -n template -a "src=/srv/motd.j2 dest=/etc/motd"
    ansible -p webservers -n template -a "src=/srv/ntp.j2 dest=/etc/ntp.conf"

Need something like the fqdn in a template?  If facter or ohai are installed, data from these projects
will also be made available to the template engine, using 'facter_' and 'ohai_' prefixes for each.

Example: Software Deployment From Source Control
================================================

Deploy your webapp straight from git

    ansible -p webservers -n git -a "repo=git://foo dest=/srv/myapp version=HEAD"

Other Modules
=============

Ansible has lots of other modules.

See the library directory for lots of extras.  There's also a manpage,
[ansible-modules(5)](https://github.com/mpdehaan/ansible/blob/master/docs/man/man5/ansible-modules.5.asciidoc) that covers all the options they take.  You can
read the asciidoc in github in the 'docs' directory.

Playbooks
=========

Playbooks are a completely different way to use ansible and are particularly awesome.

They are the basis for a really simple configuration management system, unlike
any that already exist, and one that is very well suited to deploying complex
multi-machine applications.  

An example showing a small playbook:

    ---
    - pattern: 'webservers*'
      comment: webserver setup steps
      hosts: '/etc/ansible/hosts'
      tasks:
      - name: configure template & module variables for future template calls
        action: setup http_port=80 max_clients=200
      - name: write the apache config file
        action: template src=/srv/templates/httpd.j2 dest=/etc/httpd.conf
        notify:
        - restart apache
      - name: ensure apache is running
        action: service name=httpd state=started
      handlers:
        - name: restart apache
        - action: service name=httpd state=restarted

To run a playbook:

    ansible-playbook playbook.yml

See the playbook format manpage -- [ansible-playbook(5)](https://github.com/mpdehaan/ansible/blob/master/docs/man/man5/ansible-playbook.5.asciidoc) for more details.


API
===

The Python API is very powerful:

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

Since a module can return any type of JSON data it wants, so Ansible can
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


