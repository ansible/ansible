Ansible
=======

Ansible is a extra-simple Python API for doing 'remote things' over SSH.  

As Func, which I co-wrote, aspired to avoid using SSH and have it's own daemon infrastructure, Ansible aspires to be quite different and more minimal, but still able to grow more modularly over time. 

Principles
==========

* Dead simple setup
* No server or client daemons, uses existing SSHd
* Only SSH keys are allowed for authentication
* usage of ssh-agent is more or less required
* plugins can be written in ANY language
* as with Func, API usage is an equal citizen to CLI usage

Requirements
============

* python 2.6 -- or a backport of the multiprocessing module
* paramiko

Inventory file
==============

The default inventory file (-H) is ~/.ansible_hosts and is a list
of all hostnames to target with ansible, one per line.  

This list is further filtered by the pattern wildcard (-P) to target
specific hosts.

Comamnd line usage example
==========================

Run a module by name with arguments

ansible -p "*.example.com" -m modName -a "arg1 arg2"

API Example
===========

The API is simple and returns basic datastructures.

import ansible
runner = ansible.Runner(command='inventory', host_list=['xyz.example.com', '...'])
data = runner.run()

{
    'xyz.example.com' : [ 'any kind of datastructure is returnable' ],
    'foo.example.com' : None, # failed to connect,
    ...
}

Additional options to runner include the number of forks, hostname
exclusion pattern, library path, and so on.

Parallelism
===========

Specify the number of forks to use, to run things in greater parallelism.

ansible -f 10 "*.example.com" -m modName -a "arg1 arg2"

Bundled Modules
===============

See the example library for modules, they can be written in any language
and simply return JSON to stdout.  The path to your ansible library is
specified with the "-L" flag should you wish to use a different location
than "~/ansible".

Features not supported from Func (by design)
============================================

* Delegation for treeish topologies
* Asynchronous modes for long running tasks -- background tasks on your own

Future plans
============

* Dead-simple declarative configuration management & facts engine, with
  probes implementable in any language.

Author
======

* Michael DeHaan <michael.dehaan@gmail.com> | http://michaeldehaan.net/
