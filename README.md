Ansible
=======

Ansible is a extra-simple Python API for doing 'remote things' over SSH.  

While [Func](http://fedorahosted.org/func), which I co-wrote, aspired to avoid using SSH and have it's own daemon infrastructure, Ansible aspires to be quite different and more minimal, but still able to grow more modularly over time.  This is based on talking to a lot of users of various tools and wishing to eliminate problems with connectivity and long running daemons, or not picking tool X because they preferred to code in Y.

Why use Ansible versus something else?  (Fabric, Capistrano, mCollective, Func, SaltStack, etc?) It will have far less code, it will be more correct, and it will be the easiest thing to hack on and use you'll ever see -- regardless of your favorite language of choice.  Want to only code plugins in bash or clojure?  Ansible doesn't care.  The docs will fit on one page and the source will be blindingly obvious.

Principles
==========

    * Dead simple setup
    * Super fast & parallel by default
    * No server or client daemons, uses existing SSHd
    * No additional software required on client boxes
    * Everything is self updating on the clients.  "Modules" are remotely transferred to target boxes and exec'd, and do not stay active or consume resources.
    * Only SSH keys are allowed for authentication
    * usage of ssh-agent is more or less required (no passwords)
    * plugins can be written in ANY language
    * as with Func, API usage is an equal citizen to CLI usage
    * use Python's multiprocessing capabilities to emulate Func's forkbomb logic
    * all file paths can be specified as command line options easily allowing non-root usage

Requirements
============

For the server the tool is running from, *only*:

    * python 2.6 -- or the 2.4/2.5 backport of the multiprocessing module
    * paramiko

Inventory file
==============

The inventory file is a required list of hostnames that can be potentially managed by
ansible.  Eventually this file may be editable via the CLI, but for now, is
edited with your favorite text editor.

The default inventory file (-H) is ~/.ansible_hosts and is a list
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

The API is simple and returns basic datastructures.

    import ansible
    runner = ansible.Runner(
        pattern='*',
        module_name='inventory', 
        host_list=['xyz.example.com', '...']
    )
    data = runner.run()

    {
        'xyz.example.com' : [ 'any kind of datastructure is returnable' ],
        'foo.example.com' : None, # failed to connect,
        ...
    }

Additional options to Runner include the number of forks, hostname
exclusion pattern, library path, arguments, and so on.  Read the source, it's not
complicated.

Patterns
========

To target only hosts starting with "rtp", for example:

   * ansible "rtp*" -n command -a "yum update apache"

Parallelism
===========

Specify the number of forks to use, to run things in greater parallelism.

    * ansible -f 10 "*.example.com" -n command -a "yum update apache"

10 forks.  The default is 3.  5 is right out.

File Transfer
=============

Ansible can SCP lots of files to lots of places in parallel.

   * ansible -f 10 -n copy -a "/etc/hosts /tmp/hosts"

Bundled Modules
===============

See the example library for modules, they can be written in any language
and simply return JSON to stdout.  The path to your ansible library is
specified with the "-L" flag should you wish to use a different location
than "~/ansible".  There is potential for a sizeable community to build
up around the library scripts.

Existing library modules
========================

   * command -- runs commands, giving output, return codes, and run time info
   * ping - just returns if the system is up or not
   * facter - retrieves facts about the host OS

Future plans
============

   * modules for users, groups, and files, using puppet style ensure mechanics
   * inventory gathering (w/ accompanying ansible-inventory & RSS)
   * very simple option constructing/parsing for modules
   * Dead-simple declarative configuration management engine using
     a runbook style recipe file, written in JSON or YAML
   * maybe it's own fact engine, not required, that also feeds from facter
   * add/remove/list hosts from the command line
   * list available modules from command line
   * filter exclusion (run this only if fact is true/false)

License
=======

   * MIT

Author
======

    Michael DeHaan -- michael.dehaan@gmail.com

    [http://michaeldehaan.net](http://michaeldehaan.net/)


