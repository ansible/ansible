Become (Privilege Escalation)
+++++++++++++++++++++++++++++

Ansible can use existing privilege escalation systems to allow a user to execute tasks as another.

.. contents:: Topics

Become
``````
Ansible allows you to 'become' another user, different from the user that logged into the machine (remote user). This is done using existing
privilege escalation tools, which you probably already use or have configured, like `sudo`, `su`, `pfexec`, `doas`, `pbrun`, `dzdo`, `ksu` and others.


.. note:: Before 1.9 Ansible mostly allowed the use of `sudo` and a limited use of `su` to allow a login/remote user to become a different user
    and execute tasks, create resources with the 2nd user's permissions. As of 1.9 `become` supersedes the old sudo/su, while still being backwards compatible.
    This new system also makes it easier to add other privilege escalation tools like `pbrun` (Powerbroker), `pfexec`, `dzdo` (Centrify), and others.

.. note:: Become vars & directives are independent, i.e. setting `become_user` does not set `become`.


Directives
-----------
These can be set from play to task level, but are overridden by connection variables as they can be host specific.

become
    set to 'true'/'yes' to activate privilege escalation.

become_user
    set to user with desired privileges — the user you 'become', NOT the user you login as. Does NOT imply `become: yes`, to allow it to be set at host level.

become_method
    (at play or task level) overrides the default method set in ansible.cfg, set to `sudo`/`su`/`pbrun`/`pfexec`/`doas`/`dzdo`/`ksu`

become_flags
    (at play or task level) permit to use specific flags for the tasks or role. One common use is to change user to nobody when the shell is set to no login. Added in Ansible 2.2.

For example, to manage a system service (which requires ``root`` privileges) when connected as a non-``root`` user (this takes advantage of the fact that the default value of ``become_user`` is ``root``)::

    - name: Ensure the httpd service is running
      service:
        name: httpd
        state: started
      become: true

To run a command as the ``apache`` user::

    - name: Run a command as the apache user
      command: somecommand
      become: true
      become_user: apache

To do something as the ``nobody`` user when the shell is nologin::

    - name: Run a command as nobody
      command: somecommand
      become: true
      become_method: su
      become_user: nobody
      become_flags: '-s /bin/sh'

Connection variables
--------------------
Each allows you to set an option per group and/or host, these are normally defined in inventory but can be used as normal variables.

ansible_become
    equivalent of the become directive, decides if privilege escalation is used or not.

ansible_become_method
    allows to set privilege escalation method

ansible_become_user
    allows to set the user you become through privilege escalation, does not imply `ansible_become: True`

ansible_become_pass
    allows you to set the privilege escalation password

For example, if you want to run all tasks as ``root`` on a server named ``webserver``, but you can only connect as the ``manager`` user, you could use an inventory entry like this::

    webserver ansible_user=manager ansible_become=true

Command line options
--------------------

--ask-become-pass, -K
    ask for privilege escalation password, does not imply become will be used

--become, -b
    run operations with become (no password implied)

--become-method=BECOME_METHOD
    privilege escalation method to use (default=sudo),
    valid choices: [ sudo | su | pbrun | pfexec | doas | dzdo | ksu ]

--become-user=BECOME_USER
    run operations as this user (default=root), does not imply --become/-b


For those from Pre 1.9 , sudo and su still work!
------------------------------------------------

For those using old playbooks will not need to be changed, even though they are deprecated, sudo and su directives, variables and options
will continue to work. It is recommended to move to become as they may be retired at one point.
You cannot mix directives on the same object (become and sudo) though, Ansible will complain if you try to.

Become will default to using the old sudo/su configs and variables if they exist, but will override them if you specify any of the new ones.


Limitations
-----------

Although privilege escalation is mostly intuitive, there are a few limitations
on how it works.  Users should be aware of these to avoid surprises.

Becoming an Unprivileged User
=============================

Ansible 2.0.x and below has a limitation with regards to becoming an
unprivileged user that can be a security risk if users are not aware of it.
Ansible modules are executed on the remote machine by first substituting the
parameters into the module file, then copying the file to the remote machine,
and finally executing it there.

Everything is fine if the module file is executed without using ``become``,
when the ``become_user`` is root, or when the connection to the remote machine
is made as root.  In these cases the module file is created with permissions
that only allow reading by the user and root.

The problem occurs when the ``become_user`` is an unprivileged user.  Ansible
2.0.x and below make the module file world readable in this case, as the module
file is written as the user that Ansible connects as, but the file needs to
be readable by the user Ansible is set to ``become``.

.. note:: In Ansible 2.1, this window is further narrowed: If the connection
    is made as a privileged user (root), then Ansible 2.1 and above will use
    chown to set the file's owner to the unprivileged user being switched to.
    This means both the user making the connection and the user being switched
    to via ``become`` must be unprivileged in order to trigger this problem.

If any of the parameters passed to the module are sensitive in nature, then
those pieces of data are located in a world readable module file for the
duration of the Ansible module execution.  Once the module is done executing,
Ansible will delete the temporary file.  If you trust the client machines then
there's no problem here.  If you do not trust the client machines then this is
a potential danger.

Ways to resolve this include:

* Use :ref:`pipelining`.  When pipelining is enabled, Ansible doesn't save the
  module to a temporary file on the client.  Instead it pipes the module to
  the remote python interpreter's stdin.  Pipelining does not work for
  non-python modules.

* (Available in Ansible 2.1) Install POSIX.1e filesystem acl support on the
  managed host.  If the temporary directory on the remote host is mounted with
  POSIX acls enabled and the :command:`setfacl` tool is in the remote ``PATH``
  then Ansible will use POSIX acls to share the module file with the second
  unprivileged user instead of having to make the file readable by everyone.

* Don't perform an action on the remote machine by becoming an unprivileged
  user.  Temporary files are protected by UNIX file permissions when you
  ``become`` root or do not use ``become``.  In Ansible 2.1 and above, UNIX
  file permissions are also secure if you make the connection to the managed
  machine as root and then use ``become`` to an unprivileged account.

.. warning:: Although the Solaris ZFS filesystem has filesystem ACLs, the ACLs
    are not POSIX.1e filesystem acls (they are NFSv4 ACLs instead).  Ansible
    cannot use these ACLs to manage its temp file permissions so you may have
    to resort to ``allow_world_readable_tmpfiles`` if the remote machines use ZFS.

.. versionchanged:: 2.1

In addition to the additional means of doing this securely, Ansible 2.1 also
makes it harder to unknowingly do this insecurely.  Whereas in Ansible 2.0.x
and below, Ansible will silently allow the insecure behaviour if it was unable
to find another way to share the files with the unprivileged user, in Ansible
2.1 and above Ansible defaults to issuing an error if it can't do this
securely.  If you can't make any of the changes above to resolve the problem,
and you decide that the machine you're running on is secure enough for the
modules you want to run there to be world readable, you can turn on
``allow_world_readable_tmpfiles`` in the :file:`ansible.cfg` file.  Setting
``allow_world_readable_tmpfiles`` will change this from an error into
a warning and allow the task to run as it did prior to 2.1.

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

