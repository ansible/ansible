Become (Privilege Escalation)
+++++++++++++++++++++++++++++

Ansible can use existing privilege escalation systems to allow a user to execute tasks as another.

.. contents:: Topics

Become
``````
Before 1.9 Ansible mostly allowed the use of `sudo` and a limited use of `su` to allow a login/remote user to become a different user
and execute tasks, create resources with the 2nd user's permissions. As of 1.9 `become` supersedes the old sudo/su, while still
being backwards compatible. This new system also makes it easier to add other privilege escalation tools like `pbrun` (Powerbroker),
`pfexec` and others.


New directives
--------------

become
    equivalent to adding `sudo:` or `su:` to a play or task, set to 'true'/'yes' to activate privilege escalation

become_user
    equivalent to adding 'sudo_user:' or 'su_user:' to a play or task, set to user with desired privileges

become_method
    at play or task level overrides the default method set in ansible.cfg, set to 'sudo'/'su'/'pbrun'/'pfexec'/'doas'


New ansible\_ variables
-----------------------
Each allows you to set an option per group and/or host

ansible_become
    equivalent to ansible_sudo or ansible_su, allows to force privilege escalation

ansible_become_method
    allows to set privilege escalation method

ansible_become_user
    equivalent to ansible_sudo_user or ansible_su_user, allows to set the user you become through privilege escalation

ansible_become_pass
    equivalent to ansible_sudo_pass or ansible_su_pass, allows you to set the privilege escalation password


New command line options
------------------------

--ask-become-pass
    ask for privilege escalation password

--become,-b
    run operations with become (no password implied)

--become-method=BECOME_METHOD
    privilege escalation method to use (default=sudo),
    valid choices: [ sudo | su | pbrun | pfexec | doas ]

--become-user=BECOME_USER
    run operations as this user (default=root)


sudo and su still work!
-----------------------

Old playbooks will not need to be changed, even though they are deprecated, sudo and su directives will continue to work though it
is recommended to move to become as they may be retired at one point. You cannot mix directives on the same object though, Ansible
will complain if you try to.

Become will default to using the old sudo/su configs and variables if they exist, but will override them if you specify any of the
new ones.



Limitations
-----------

Although privilege escalation is mostly intuitive, there are a few limitations
on how it works.  Users should be aware of these to avoid surprises.

Becoming an Unprivileged User
=============================

Ansible has a limitation with regards to becoming an
unprivileged user that can be a security risk if users are not aware of it.
Ansible modules are executed on the remote machine by first substituting the
parameters into the module file, then copying the file to the remote machine,
and finally executing it there.  If the module file is executed without using
become, when the become user is root, or when the connection to the remote
machine is made as root then the module file is created with permissions that
only allow reading by the user and root.

If the become user is an unprivileged user and then Ansible has no choice but
to make the module file world readable as there's no other way for the user
Ansible connects as to save the file so that the user that we're becoming can
read it.

If any of the parameters passed to the module are sensitive in nature then
those pieces of data are readable by reading the module file for the duration
of the Ansible module execution.  Once the module is done executing Ansible
will delete the temporary file.  If you trust the client machines then there's
no problem here.  If you do not trust the client machines then this is
a potential danger.

Ways to resolve this include:

* Use :ref:`pipelining`.  When pipelining is enabled, Ansible doesn't save the
  module to a temporary file on the client.  Instead it pipes the module to
  the remote python interpreter's stdin.  Pipelining does not work for
  non-python modules.

* Don't perform an action on the remote machine by becoming an unprivileged
  user.  Temporary files are protected by UNIX file permissions when you
  become root or do not use become.

Connection Plugin Support
=========================

Privilege escalation methods must also be supported by the connection plugin
used.   Most connection plugins will warn if they do not support become.  Some
will just ignore it as they always run as root (jail, chroot, etc).

Only one method may be enabled per host
=======================================

Methods cannot be chained.  You cannot use ``sudo /bin/su -`` to become a user,
you need to have privileges to run the command as that user in sudo or be able
to su directly to it (the same for pbrun, pfexec or other supported methods).

Can't limit escalation to certain commands
==========================================

Privilege escalation permissions have to be general.  Ansible does not always
use a specific command to do something but runs modules (code) from
a temporary file name which changes every time.  If you have '/sbin/service'
or '/bin/chmod' as the allowed commands this will fail with ansible as those
paths won't match with the temporary file that ansible creates to run the
module.


.. seealso::

   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

