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



.. note:: Privilege escalation methods must also be supported by the connection plugin used, most will warn if they do not, some will just ignore it as they always run as root (jail, chroot, etc).

.. note:: Methods cannot be chained, you cannot use 'sudo /bin/su -' to become a user, you need to have privileges to run the command as that user in sudo or be able to su directly to it (the same for pbrun, pfexec or other supported methods).

.. note:: Privilege escalation permissions have to be general, Ansible does not always use a specific command to do something but runs modules (code) from a temporary file name which changes every time. So if you have '/sbin/service' or '/bin/chmod' as the allowed commands this will fail with ansible.

.. seealso::

   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

