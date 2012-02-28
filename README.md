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

Inventory file
==============

To use ansible you must have a list of hosts somewhere.  The default inventory file (override with -H) is /etc/ansible/hosts and is a list of all hostnames to manage with ansible, one per line.  These can be hostnames or IPs.

Example:

    abc.example.com
    def.example.com
    192.168.10.50
    192.168.10.51

This list is further filtered by the pattern wildcard (-p) to target
specific hosts.  This is covered below.  You can also organize groups of systems by having multiple inventory files (i.e. keeping webservers different from dbservers, etc)

Massive Parallelism, Pattern Matching, and a Usage Example
==========================================================

Reboot all web servers in Atlanta, 10 at a time:
 
    ssh-agent bash
    ssh-add ~/.ssh/id_rsa.pub
    ansible -p "atlanta-web*" -f 10 -n command -a "/sbin/reboot"

Other than the comamnd module, though, ansible modules are not scripts.  They make
the remote system look like you state, and run the commands neccessary to get it 
there.

File Transfer
=============

Ansible can SCP lots of files to lots of places in parallel.

    ansible -p "web-*.acme.net" -f 10 -n copy -a "/etc/hosts /tmp/hosts"

Templating
==========

JSON files can be placed for template metadata using Jinja2.  Variables
placed by 'setup' can be reused between ansible runs.

    ansible -p "*" -n setup -a "favcolor=red ntp_server=192.168.1.1"
    ansible -p "*" -n template /srv/motd.j2 /etc/motd 
    ansible -p "*" -n template /srv/ntp.j2 /etc/ntp.conf

Need something like the fqdn in a template?  If facter or ohai are installed, data from these projects
will also be made available to the template engine, using 'facter_' and 'ohai_'
prefixes for each.

Git Deployments
===============

Deploy your webapp straight from git

    ansible -p "web*" -n git -a "repo=git://foo dest=/srv/myapp version=HEAD"

Take Inventory
==============

Run popular open-source data discovery tools across a wide number of hosts.
This is best used from API scripts that want to learn about remote systems.

    ansible -p "dbserver*" -n facter
    ansible -p "dbserver"" -n ohai

Other Modules
=============

See the library directory for lots of extras.  There's also a manpage,
ansible-modules(5) that covers all the options they take.  You can
read the asciidoc in github in the 'docs' directory.

Playbooks
=========

Playbooks are particularly awesome.  Playbooks can batch ansible commands
together, and can even fire off triggers when certain commands report changes.
They are the basis for a really simple configuration management system, unlike
any that already exist.  Powerful, concise, but dead simple.

See examples/playbook.yml for what the syntax looks like, and the manpage -- ansible-playbook(5) for more details.

To run a playbook:

    ansible -r playbook.yml


Future plans
============

See github's issue tracker for what we're thinking about

License
=======

MIT

Mailing List
============

Join the mailing list to talk about Ansible!

[ansible-project](http://groups.google.com/group/ansible-project)

Author
======

Michael DeHaan -- michael.dehaan@gmail.com

[http://michaeldehaan.net](http://michaeldehaan.net/)


