.. image:: http://ansible.github.com/mpd_rings.jpg
   :height: 225
   :width: 300
   :alt: ""
   :target: http://photos.michaeldehaan.net/infrared/h3d850bdf#h3d850bdf
.. image:: http://ansible.github.com/mpd_tunnel.jpg
   :height: 225
   :width: 337
   :alt: "" 
   :target: http://photos.michaeldehaan.net/favorites/h2428aca7#h2428aca7
.. image:: http://ansible.github.com/mpd_tubes.jpg
   :height: 225
   :width: 225
   :alt: "" 
   :target: http://photos.michaeldehaan.net/ncsu/h3b63b68e#h3b63b68e

Introducing Ansible
===================

Ansible is a radically simple deployment, model-driven configuration management, 
and command execution framework. Other tools in this space have been too
complicated for too long, require too much bootstrapping, and have too
much learning curve.  Ansible is dead simple and painless to extend.
For comparison, Puppet and Chef have about 60k lines of code.
Ansible's core is a little over 1000 lines.

Ansible isn't just for idempotent configuration -- it's also great for ad-hoc
tasks, quickly firing off commands against nodes.  See :doc:`examples`.
Where Ansible excels though, is expressing complex multi-node 
deployment processes, executing ordered sequences on 
different sets of nodes through :doc:`playbooks`.

Extending ansible does not require programming in any particular
language -- you can write :doc:`modules` as scripts or programs that return
simple JSON.  It's also trivially easy to just execute useful shell
commands.

Why use Ansible versus something else?  (Puppet, Chef, Fabric,
Capistrano, mCollective, Func, SaltStack, etc?) Ansible will have far
less code, it will be (by extension) more correct, and it will be the
easiest thing to hack on and use you'll ever see -- regardless of your
favorite language of choice.

Systems management doesn't have to be complicated.  Ansible's docs
will remain short & simple, and the source will be blindingly obvious.

Architecture
````````````

.. image:: http://ansible.github.com/ansible_arch.jpg
   :alt: "Architecture Diagram" 
   :width: 648
   :height: 464


Features
````````

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
`````````

Your ideas and contributions are welcome.  We're also happy to help 
you with questions about Ansible.

* Join the `ansible-project mailing list <http://groups.google.com/group/ansible-project>`_ on Google Groups
* Join `#ansible <irc://irc.freenode.net/#ansible>`_ on the `freenode IRC network <http://freenode.net/>`_
* Visit the `project page <https://github.com/ansible/ansible>`_ on Github

  - View the `issue tracker <https://github.com/ansible/ansible/issues>`_


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
   man

About the Author
````````````````

Ansible was originally developed by `Michael DeHaan <http://michaeldehaan.net>`_ (`@laserllama <http://twitter.com/#!/laserllama>`_), a Raleigh, NC
based software developer and architect.  He created other popular
DevOps programs such as `Cobbler <http://cobbler.github.com/>`_, the popular Linux install server.
Cobbler is used to deploy mission critical systems all over the
planet, in industries ranging from massively multiplayer gaming, core
internet infrastructure, finance, chip design, and more.  Michael also
helped co-author of `Func <http://fedorahosted.org/func/>`_, a precursor to Ansible, which is used to
orchestrate systems in lots of diverse places.  He's worked on systems
software for IBM, Motorola, Red Hat's Emerging Technologies Group,
Puppet Labs, and rPath.  Reach Michael by email `here <mailto:michael.dehaan@gmail.com>`_.
