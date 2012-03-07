.. Director documentation master file, created by sphinx-quickstart on Sat Sep 27 13:23:22 2008.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Ansible
=======

Ansible is a extra-simple tool/API for doing 'parallel remote things'
over SSH -- whether executing commands, running "modules", or
executing larger 'playbooks' that can serve as a configuration
management or deployment system.

While `Func installation <http://fedorahosted.org/func>`_ which I
co-wrote, aspired to avoid using SSH and have it's own daemon
infrastructure, Ansible aspires to be quite different and more
minimal, but still able to grow more modularly over time.  This is
based on talking to a lot of users of various tools and wishing to
eliminate problems with connectivity and long running daemons, or not
picking tool X because they preferred to code in Y. Further, playbooks
take things a whole step further, building the config and deployment
system I always wanted to build.

Why use Ansible versus something else?  (Fabric, Capistrano,
mCollective, Func, SaltStack, etc?) It will have far less code, it
will be more correct, and it will be the easiest thing to hack on and
use you'll ever see -- regardless of your favorite language of choice.
Want to only code plugins in bash or clojure?  Ansible doesn't care.
The docs will fit on one page and the source will be blindingly
obvious.


Design Principles
`````````````````

* Dead simple setup
* Super fast & parallel by default
* No server or client daemons; use existing SSHd
* No additional software required on client boxes
* Modules can be written in ANY language
* Awesome API for creating very powerful distributed scripts
* Be usable as non-root
* Create the easiest config management system to use, ever.


Requirements
````````````

Requirements are extremely minimal.

If you are running python 2.6 on the **overlord** machine, you will
need:

* ``paramiko``
* ``PyYAML``
* ``Asciidoc`` (for building documentation)

If you are running less than Python 2.6, you will also need:

* The Python 2.4 or 2.5 backport of the multiprocessing module
  * `Installation and Testing Instructions <http://code.google.com/p/python-multiprocessing/wiki/Install>`_
* ``simplejson``

On the managed nodes, to use templating, you will need:

* ``python-jinja2`` (you can install this with ansible)


Getting Ansible
```````````````

Tagged releases are available as tar.gz files from the Ansible github
project page:

* `Ansible/downloads <https://github.com/ansible/ansible/downloads>`_

You can also clone the git repository yourself and install Ansible in
one of two ways:


Python Distutils
++++++++++++++++

You can install Ansible using Python Distutils::

    $ git clone git://github.com/ansible/ansible.git
    $ cd ./ansible
    $ sudo make install


Via RPM
+++++++

In the future, pre-built RPMs may be available. Until that time you
can use the ``make rpm`` command::

    $ git clone git://github.com/ansible/ansible.git
    $ cd ./ansible
    $ make rpm
    $ sudo rpm -Uvh ~/rpmbuild/RPMS/noarch/ansible-1.0-1.noarch.rpm
 

Contents
========

.. toctree::
   :maxdepth: 3

   gettingstarted
   YAMLScripts
   patterns
   modules
   playbooks
   examples
   api
   communicate
   man


Communicate or Get Involved
===========================

* Join the `ansible-project mailing list <http://groups.google.com/group/ansible-project>`_ on Google Groups
* Join `#ansible <irc://irc.freenode.net/#ansible>`_ on the `freenode IRC network <http://freenode.net/>`_
* Visit the `project page <https://github.com/ansible/ansible>`_ on Github

  - View the `issue tracker <https://github.com/ansible/ansible/issues>`_
