
Ansible is a radically simple deployment, model-driven configuration management, 
and command execution framework. Other tools in this space have been too
complicated for too long, require too much bootstrapping, and have too
much learning curve.  Ansible is dead simple and painless to extend.
For comparison, Puppet and Chef have about 60k lines of code.
Ansible's core is a little over 1000 lines.

Ansible isn't just for idempotent configuration -- it's also great for ad-hoc
tasks, quickly firing off commands against nodes.  See :doc:`examples`.

Innovative Multi-node Control
`````````````````````````````

Where Ansible excels though, is expressing complex multi-node 
deployment processes, executing ordered sequences on 
different sets of nodes through :doc:`playbooks`.   Playbooks contain one or
more plays, each executed against a different batch of nodes.  Think about
webservers, database servers, and backend servers in a multi-node web environment.  A play can address each set of machines in a cycle, ensuring the configurations of the machines were correct and also updating them to the specified
version of software if required.

Multi-machine software deployment is poorly solved by most systems management tools -- often due to architectural nature of being pull oriented and having complex ordering systems, they cover configuration  but fail at deployment when updating tiers of machines in well defined steps. This results in using two (or more) logically distinct tools and having complex overlap between them.  

Deployment and Configuration, Unified
`````````````````````````````````````

Other deployment (compared to config) oriented frameworks similarly cover deployment well but lack a strongly defined resource model and devolve into glorified remote scripts.  Ansible playbooks -- having been designed with this problem in mind -- are good at both deployment & idempotent configuration, meaning you don't have to spread your infrastructure management out between different tools (Puppet+Capistrano, Chef+Fabric, etc), and performing ordered steps between different classes of machines is no problem, yet our modules affect system state only when required -- while avoiding the problem of fragile scripting that assumes certain starting
or ending states.

Ansible is also unique in other ways.  Extending ansible does not require programming in any particular language -- you can write :doc:`modules` as idempotent scripts or programs that return simple JSON.   Ansible is also pragmatic, so when you need to, it's also trivially easy to just execute useful shell commands.

Why use Ansible versus other configuration management tools?  (Puppet, Chef, etc?) Ansible will have far
less code, it will be (by extension) more correct, and it will be the
easiest thing to hack on and use you'll ever see -- regardless of your
favorite language of choice.  Versus other deployment tools?  (Capistrano, Fabric?).  Ansible playbooks are easier
to use (not being code) and also allows intermixing of idempotent configuration management rules for a higher level
of control.  Further, it was designed for deploying multi-node applications from the beginning.

Simple & Secure By Default
``````````````````````````

Compared with most configuration managememnt tools, Ansible is also much more secure.  While most configuration management tools use a daemon, running as root with full access to the system, with its own in-house developed PKI infrastructure, Ansible just uses SSH (and supports sudo as neccesssary).  There is no additional attack surface and OpenSSH is one of the most peer reviewed security components out there.
If a central server containing your playbooks are comprimised, your nodes are not -- which is NOT the case
of these other tools, which can, more or less, turn into a botnet.  Our security approach is to avoid writing custom
crypto code altogether, and rely on the most secure part of the Linux/Unix subsystem that your machines are already using.  There is no PKI subsystem to maintain, which can be a frequent source of problems, particularly when reinstalling or migrating
hosts.  

Systems management doesn't have to be complicated.  Ansible's docs will remain short & simple, and the source will be blindingly obvious.  We've learned well from "Infrastructure is Code".  Infrastructure should be easy and powerful to command, but it should not look like code, lest it acquire the disadvantages of a software project -- bugs, complexity, and overhead.  Infrastructure configurations should be simple, easy to develop, and easy to audit.


Architecture
============

.. image:: http://ansible.github.com/ansible_arch2.jpg
   :alt: "Architecture Diagram" 
   :width: 800
   :align: center

Features
========

* Dead simple setup
* Super fast & parallel by default
* No server or client daemons; use existing SSHd out of the box
* No additional software required on client boxes
* Can be easily run from a checkout, no installation required
* Modules are idempotent, but you can also easily use shell commands
* Modules can be written in ANY language
* Awesome API for creating very powerful distributed scripts
* Does not have to run remote steps as root
* Pluggable transports (SSH is just the default)
* Source host info & variables from files or external software
* The easiest config management system to use, ever.


Resources
=========

Your ideas and contributions are welcome.  We're also happy to help 
you with questions about Ansible.

* Visit the `project page <https://github.com/ansible/ansible>`_ on Github
* View the `issue tracker <https://github.com/ansible/ansible/issues>`_
* See the presentation on `Speakerdeck <http://speakerdeck.com/u/mpdehaan/p/ansible>`_
* Visit the `Google Group <http://groups.google.com/group/ansible-project>`_
* Chat on `FreeNode <http://webchat.freenode.net/?channels=ansible>`_

.. raw:: html

   <img src="http://groups.google.com/intl/en/images/logos/groups_logo_sm.gif" height=30 width=140 alt="Google Groups">
   <br/>
   <b>Subscribe to Ansible Project</b>
   <br/>
   <form action="http://groups.google.com/group/ansible-project/boxsubscribe">
   <br/>
   Email: <input type=text name=email>&nbsp;&nbsp;<input type=submit name="sub" value="Subscribe">
   <br/></br>
   </form>
   <br/>


Contents
========

.. toctree::
   :maxdepth: 3

   gettingstarted
   patterns
   examples
   modules
   YAMLSyntax
   playbooks
   api
   moduledev
   faq

About the Author
================

Ansible was originally developed by `Michael DeHaan <http://michaeldehaan.net>`_ (`@laserllama <http://twitter.com/#!/laserllama>`_), a Raleigh, NC
based software developer and architect.  He created the popular
DevOps program `Cobbler <http://cobbler.github.com/>`_.
Cobbler is used to deploy mission critical systems all over the
planet, in industries ranging from massively multiplayer gaming, core
internet infrastructure, finance, chip design, and more.  Michael also
helped co-author `Func <http://fedorahosted.org/func/>`_, a precursor to Ansible, which is used to
orchestrate systems in lots of diverse places.  He's worked on systems
software for IBM, Motorola, Red Hat's Emerging Technologies Group,
Puppet Labs, and rPath.  Reach Michael by email `here <mailto:michael.dehaan@gmail.com>`_.
