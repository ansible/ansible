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

* paramiko
* python-jinja2
* PyYAML (if using playbooks)

If you are running less than Python 2.6, you will also need

* the Python 2.4 or 2.5 backport of the multiprocessing module
* simplejson

On the managed nodes, to use templating, you will need:

* python-jinja2 (you can install this with ansible)



Contents:

.. toctree::
   :maxdepth: 3

   gettingstarted
   YAMLScripts
   patterns
   modules
   playbooks
   api
   communicate
   examples
   man

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

