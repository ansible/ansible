*****************************
Become (Privilege Escalation)
*****************************

Ansible can use existing privilege escalation systems to allow a user to execute tasks as another.

.. contents:: Topics

Become
======

Ansible allows you to 'become' another user, different from the user that logged into the machine (remote user). This is done using existing privilege escalation tools such as `sudo`, `su`, `pfexec`, `doas`, `pbrun`, `dzdo`, `ksu`, `runas` and others.


.. note:: Prior to version 1.9, Ansible mostly allowed the use of `sudo` and a limited use of `su` to allow a login/remote user to become a different user and execute tasks and create resources with the second user's permissions. As of Ansible version 1.9,  `become` supersedes the old sudo/su, while still being backwards compatible. This new implementation also makes it easier to add other privilege escalation tools, including `pbrun` (Powerbroker), `pfexec`, `dzdo` (Centrify), and others.

.. note:: Become vars and directives are independent. For example, setting ``become_user`` does not set ``become``.


Directives
==========

These can be set from play to task level, but are overridden by connection variables as they can be host specific.

become
    set to ``yes`` to activate privilege escalation.

become_user
    set to user with desired privileges — the user you `become`, NOT the user you login as. Does NOT imply ``become: yes``, to allow it to be set at host level.

become_method
    (at play or task level) overrides the default method set in ansible.cfg, set to `sudo`/`su`/`pbrun`/`pfexec`/`doas`/`dzdo`/`ksu`/`runas`

become_flags
    (at play or task level) permit the use of specific flags for the tasks or role. One common use is to change the user to nobody when the shell is set to no login. Added in Ansible 2.2.

For example, to manage a system service (which requires ``root`` privileges) when connected as a non-``root`` user (this takes advantage of the fact that the default value of ``become_user`` is ``root``)::

    - name: Ensure the httpd service is running
      service:
        name: httpd
        state: started
      become: yes

To run a command as the ``apache`` user::

    - name: Run a command as the apache user
      command: somecommand
      become: yes
      become_user: apache

To do something as the ``nobody`` user when the shell is nologin::

    - name: Run a command as nobody
      command: somecommand
      become: yes
      become_method: su
      become_user: nobody
      become_flags: '-s /bin/sh'

Connection variables
--------------------
Each allows you to set an option per group and/or host, these are normally defined in inventory but can be used as normal variables.

ansible_become
    equivalent of the become directive, decides if privilege escalation is used or not.

ansible_become_method
    which privilege escalation method should be used

ansible_become_user
    set the user you become through privilege escalation; does not imply ``ansible_become: yes``

ansible_become_pass
    set the privilege escalation password. See :doc:`playbooks_vault` for details on how to avoid having secrets in plain text

For example, if you want to run all tasks as ``root`` on a server named ``webserver``, but you can only connect as the ``manager`` user, you could use an inventory entry like this::

    webserver ansible_user=manager ansible_become=yes

Command line options
--------------------

--ask-become-pass, -K
    ask for privilege escalation password; does not imply become will be used. Note that this password will be used for all hosts.

--become, -b
    run operations with become (no password implied)

--become-method=BECOME_METHOD
    privilege escalation method to use (default=sudo),
    valid choices: [ sudo | su | pbrun | pfexec | doas | dzdo | ksu | runas ]

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^

Privilege escalation methods must also be supported by the connection plugin
used.   Most connection plugins will warn if they do not support become.  Some
will just ignore it as they always run as root (jail, chroot, etc).

Only one method may be enabled per host
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Methods cannot be chained.  You cannot use ``sudo /bin/su -`` to become a user,
you need to have privileges to run the command as that user in sudo or be able
to su directly to it (the same for pbrun, pfexec or other supported methods).

Can't limit escalation to certain commands
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Privilege escalation permissions have to be general.  Ansible does not always
use a specific command to do something but runs modules (code) from
a temporary file name which changes every time.  If you have '/sbin/service'
or '/bin/chmod' as the allowed commands this will fail with ansible as those
paths won't match with the temporary file that ansible creates to run the
module.

.. _become-network:

Become and Networks
===================


network_cli and become
----------------------

Ansible 2.5 added support for ``become`` to be used to enter `enable` mode (Privileged EXEC mode) on network devices that support it. This replaces the previous ``authorize`` and ``auth_pass`` options in ``provider``.

This functionality requires the host connection type to be using ``connection: network_cli``. In Ansible 2.5 this is limited to ``eos`` and ``ios``.

This allows privileges to be raised for the specific tasks that need them. Adding ``become: yes`` and ``become_method: enable`` informs Ansible to go into privilege mode before executing the task.

If a task fails with the following then it's an indicator that `enable` mode is required:

.. code-block:: console

   Invalid input (privileged mode required)

The following example shows how to set enable mode for a specific task:

.. code-block:: yaml

   - name: Gather facts (eos)
     eos_facts:
       gather_subset:
         - "!hardware"
     become: yes
     become_method: enable

The following example shows how to set enable mode for `all` tests in this play:

.. code-block:: yaml

   - hosts: eos-switches
     become: yes
     become_method: enable
     tasks:
       - name: Gather facts (eos)
         eos_facts:
           gather_subset:
             - "!hardware"

Setting enable mode for all tasks
---------------------------------

Often you wish for all tasks to run using privilege mode, that is best achieved by using ``group_vars``:

**group_vars/eos.yml**

.. code-block:: yaml

   ansible_connection: network_cli
   ansible_network_os: eos
   ansible_user: myuser
   ansible_become: yes
   ansible_become_method: enable


Passwords for enable mode
^^^^^^^^^^^^^^^^^^^^^^^^^

If a password is required to enter enable mode this can be specified by doing one of the following:

* providing the :option:`--ask-become-pass <ansible-playbook --ask-become-pass>` command line option
* setting the ``ansible_become_pass`` connection variable

.. warning::

   As a reminder passwords should never be stored in plain text. See how encrypt secrets in vault :doc:`playbooks_vault` for more information.

For more information about ``network_cli`` see :ref:`network-cli`.

.. _become-network-auth-and-auth-password:

authorize and auth_pass
-----------------------

For network platforms that do not currently support ``connection: network_cli`` then the module options ``authorize`` and ``auth_pass`` can be used.

.. code-block:: yaml

   - hosts: eos-switches
     ansible_connection: local
     tasks:
       - name: Gather facts (eos)
         eos_facts:
           gather_subset:
             - "!hardware"
         provider:
           authorize: yes
           auth_pass: " {{ secret_auth_pass }}"

Note that over time more platforms will move to support ``become``. Check the :doc:`list_of_network_modules` for details.

.. _become-windows:

Become and Windows
==================

Since Ansible 2.3, ``become`` can be used on Windows hosts through the
``runas`` method. Become on Windows uses the same inventory setup and
invocation arguments as ``become`` on a non-Windows host, so the setup and
variable names are the same as what is defined in this document.

While ``become`` can be used to assume the identity of another user, there are other uses for
it with Windows hosts. One important use is to bypass some of the
limitations that are imposed when running on WinRM, such as constrained network
delegation or accessing forbidden system calls like the WUA API. You can use
``become`` with the same user as ``ansible_user`` to bypass these limitations
and run commands that are not normally accessible in a WinRM session.

.. note:: Prior to Ansible 2.4, become would only work when ``ansible_winrm_transport`` was
    set to either ``basic`` or ``credssp``, but since Ansible 2.4 become now works on
    all transport types.

Administrative Rights
---------------------

Many tasks in Windows require administrative privileges to complete. When using
the ``runas`` become method, Ansible will attempt to run the module with the
full privileges that are available to the remote user. If it fails to elevate
the user token, it will continue to use the limited token during execution.

Before Ansible 2.5, a token was only able to be elevated when UAC was disabled
or the remote user had the ``SeTcbPrivilege`` assigned. This restriction has
been lifted in Ansible 2.5 and a user that is a member of the
``BUILTIN\Administrators`` group should have an elevated token during the
module execution.

To determine the type of token that Ansible was able to get, run the following
task and check the output::

    - win_shell: cmd.exe /c whoami && whoami /groups && whoami /priv
      become: yes

Under the ``GROUP INFORMATION`` section, the ``Mandatory Label`` entry
determines whether the user has Administrative rights. Here are the labels that
can be returned and what they mean:

* ``Medium``: Ansible failed to get an elevated token and ran under a limited
  token. Only a subset of the privileges assigned to user are available during
  the module execution and the user does not have administrative rights.

* ``High``: An elevated token was used and all the privileges assigned to the
  user are available during the module execution.

* ``System``: The ``NT AUTHORITY\System`` account is used and has the highest
  level of privileges available.

The output will also show the list of privileges that have been granted to the
user. When ``State==Disabled``, the privileges have not been enabled but can be
if required. In most scenarios these privileges are automatically enabled when
required.

If running on a version of Ansible that is older than 2.5 or the normal
``runas`` escalation process fails, an elevated token can be retrieved by:

* Set the ``become_user`` to ``System`` which has full control over the
  operating system.

* Grant ``SeTcbPrivilege`` to the user Ansible connects with on
  WinRM. ``SeTcbPrivilege`` is a high-level privilege that grants
  full control over the operating system. No user is given this privilege by
  default, and care should be taken if you grant this privilege to a user or group.
  For more information on this privilege, please see
  `Act as part of the operating system <https://technet.microsoft.com/en-us/library/dn221957(v=ws.11).aspx>`_.
  You can use the below task to set this privilege on a Windows host::

    - name: grant the ansible user the SeTcbPrivilege right
      win_user_right:
        name: SeTcbPrivilege
        users: '{{ansible_user}}'
        action: add

* Turn UAC off on the host and reboot before trying to become the user. UAC is
  a security protocol that is designed to run accounts with the
  ``least privilege`` principle. You can turn UAC off by running the following
  tasks::

    - name: turn UAC off
      win_regedit:
        path: HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\policies\system
        name: EnableLUA
        data: 0
        type: dword
        state: present
      register: uac_result

    - name: reboot after disabling UAC
      win_reboot:
      when: uac_result is changed

.. Note:: Granting the ``SeTcbPrivilege`` or turning UAC off can cause Windows
    security vulnerabilities and care should be given if these steps are taken.

Local Service Accounts
----------------------

Prior to Ansible version 2.5, ``become`` only worked with a local or domain
user account. Local service accounts like ``System`` or ``NetworkService``
could not be used as ``become_user`` in these older versions. This restriction
has been lifted since the 2.5 release of Ansible. The three service accounts
that can be set under ``become_user`` are:

* System
* NetworkService
* LocalService

Because local service accounts do not have passwords, the
``ansible_become_password`` parameter is not required and is ignored if
specified.

Limitations
-----------

Be aware of the following limitations with ``become`` on Windows:

* Running a task with ``async`` and ``become`` on Windows Server 2008, 2008 R2
  and Windows 7 does not work.

* The become user logs on with an interactive session, so it must have the
  ability to do so on the Windows host. If it does not inherit the
  ``SeAllowLogOnLocally`` privilege or inherits the ``SeDenyLogOnLocally``
  privilege, the become process will fail.

* Prior to Ansible version 2.3, become only worked when
  ``ansible_winrm_transport`` was either ``basic`` or ``credssp``. This
  restriction has been lifted since the 2.4 release of Ansible for all hosts
  except Windows Server 2008 (non R2 version).

.. seealso::

   `Mailing List <https://groups.google.com/forum/#!forum/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `webchat.freenode.net <https://webchat.freenode.net>`_
       #ansible IRC chat channel

