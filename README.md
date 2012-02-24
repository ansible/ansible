Ansible
=======

Ansible is a extra-simple Python API for doing 'remote things' over SSH.  

While [Func](http://fedorahosted.org/func), which I co-wrote, 
aspired to avoid using SSH and have it's own daemon infrastructure, 
Ansible aspires to be quite different and more minimal, but still able 
to grow more modularly over time.  This is based on talking to a lot of 
users of various tools and wishing to eliminate problems with connectivity 
and long running daemons, or not picking tool X because they preferred to 
code in Y.

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
    * No server or client daemons, uses existing SSHd
    * No additional software required on client boxes
    * Everything is self updating on the clients  
    * Encourages use of ssh-agent
    * Plugins can be written in ANY language
    * API usage is an equal citizen to CLI usage
    * Can be controlled/installed/used as non-root

Requirements
============

For the server the tool is running from, *only*:

    * python 2.6 -- or the 2.4/2.5 backport of the multiprocessing module
    * PyYAML (if using playbooks)
    * paramiko

Inventory file
==============

The inventory file is a required list of hostnames that can be 
potentially managed by ansible.  Eventually this file may be editable 
via the CLI, but for now, is edited with your favorite text editor.

The default inventory file (-H) is /etc/ansible/hosts and is a list
of all hostnames to target with ansible, one per line.  These
can be hostnames or IPs

Example:

    abc.example.com
    def.example.com
    192.168.10.50
    192.168.10.51

This list is further filtered by the pattern wildcard (-P) to target
specific hosts.  This is covered below.

You can organize groups of systems by having multiple inventory
files (i.e. keeping webservers different from dbservers, etc)

Command line usage example
==========================

Run a module by name with arguments
 
   * ssh-agent bash
   * ssh-add ~/.ssh/id_rsa.pub
   * ansible -p "*.example.com" -n modName -a "arg1 arg2"

API Example
===========

The API is simple and returns basic datastructures.  Ansible will keep
track of which hosts were successfully contacted seperately from hosts
that had communication problems.  The format of the return, if successful,
is entirely up to the module.

    import ansible
    runner = ansible.Runner(
        pattern='*',
        module_name='inventory',
        module_args='...' 
    )
    data = runner.run()

    { 
        'contacted' : {
            'xyz.example.com' : [ 'any kind of datastructure is returnable' ],
            'foo.example.com' : [ '...' ]
        },
        'dark' : {
            'bar.example.com' : [ 'failure message' ]
        }
    }

Additional options to Runner include the number of forks, hostname
exclusion pattern, library path, arguments, and so on.  

Read the source, it's not complicated.

Patterns
========

To target only hosts starting with "rtp", for example:

   * ansible -p "rtp*" -n command -a "yum update apache"

Parallelism
===========

Specify the number of forks to use, to run things in greater parallelism.

    * ansible -f 10 "*.example.com" -n command -a "yum update apache"

10 forks.  The default is 3.  5 is right out.

File Transfer
=============

Ansible can SCP lots of files to lots of places in parallel.

   * ansible -p "web-*.acme.net" -f 10 -n copy -a "/etc/hosts /tmp/hosts"

Ansible Library (Bundled Modules)
=================================

See the example library for modules, they can be written in any language
and simply return JSON to stdout.  The path to your ansible library is
specified with the "-L" flag should you wish to use a different location
than "/usr/share/ansible".  This means anyone can use Ansible, even without
root permissions.

There is potential for a sizeable community to build 
up around the library scripts.

Modules include:

   * command -- runs commands, giving output, return codes, and run time info
   * ping - just returns if the system is up or not
   * facter - retrieves facts about the host OS
   * copy - add files to remote systems

Playbooks
=========

Playbooks are loosely equivalent to recipes or manifests in most configuration
management or deployment tools and describe a set of operations to run on
a set of hosts.  Some tasks can choose to only fire when certain
conditions are true, and if a task in a chain fails the dependent tasks
will not proceed.  Playbooks are described in (YAML)[http://yaml.org] format.

Future plans
============

   * see TODO.md

License
=======

   * MIT

Author
======

Michael DeHaan -- michael.dehaan@gmail.com

[http://michaeldehaan.net](http://michaeldehaan.net/)


