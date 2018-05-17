.. _become:

**********************************
Understanding Privilege Escalation
**********************************

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

* Use `pipelining`.  When pipelining is enabled, Ansible doesn't save the
  module to a temporary file on the client.  Instead it pipes the module to
  the remote python interpreter's stdin. Pipelining does not work for
  python modules involving file transfer (for example: :ref:`copy <copy_module>`,
  :ref:`fetch <fetch_module>`, :ref:`template <template_module>`), or for non-python modules.

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

As of version 2.6, Ansible supports ``become`` for privilege escalation (entering ``enable`` mode or privileged EXEC mode) on all :ref:`Ansible-maintained platforms<network_supported>` that support ``enable`` mode: `eos``, ``ios``, and ``nxos``. Using ``become`` replaces the ``authorize`` and ``auth_pass`` options in a ``provider`` dictionary.

You must set the connection type to either ``connection: network_cli`` or ``connection: httpapi`` to use ``become`` for privilege escalation on network devices. Check the :ref:`platform_options` and :ref:`network_modules` documentation for details.

You can use escalated privileges on only the specific tasks that need them, on an entire play, or on all plays. Adding ``become: yes`` and ``become_method: enable`` instructs Ansible to enter ``enable`` mode before executing the task, play, or playbook where those parameters are set.

If you see this error message, the task that generated it requires ``enable`` mode to succeed:

.. code-block:: console

   Invalid input (privileged mode required)

To set ``enable`` mode for a specific task, add ``become`` at the task level:

.. code-block:: yaml

   - name: Gather facts (eos)
     eos_facts:
       gather_subset:
         - "!hardware"
     become: yes
     become_method: enable

To set enable mode for all tasks in a single play, add ``become`` at the play level:

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

Often you wish for all tasks in all plays to run using privilege mode, that is best achieved by using ``group_vars``:

**group_vars/eos.yml**

.. code-block:: yaml

   ansible_connection: network_cli
   ansible_network_os: eos
   ansible_user: myuser
   ansible_become: yes
   ansible_become_method: enable


Passwords for enable mode
^^^^^^^^^^^^^^^^^^^^^^^^^

If you need a password to enter ``enable`` mode, you can specify it in one of two ways:

* providing the :option:`--ask-become-pass <ansible-playbook --ask-become-pass>` command line option
* setting the ``ansible_become_pass`` connection variable

.. warning::

   As a reminder passwords should never be stored in plain text. For information on encrypting your passwords and other secrets with Ansible Vault, see :doc:`playbooks_vault`.

authorize and auth_pass
-----------------------

Ansible still supports ``enable`` mode with ``connection: local`` for legacy playbooks. To enter ``enable`` mode with ``connection: local``, use the module options ``authorize`` and ``auth_pass``:

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

We recommend updating your playbooks to use ``become`` for network-device ``enable`` mode consistently. The use of ``authorize`` and of ``provider`` dictionaries will be deprecated in future. Check the :ref:`platform_options` and :ref:`network_modules` documentation for details.

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

    - win_whoami:
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

Accounts without a Password
---------------------------

.. Warning:: As a general security best practice, you should avoid allowing accounts without passwords.

Ansible can be used to become an account that does not have a password (like the
``Guest`` account). To become an account without a password, set up the
variables like normal but either do not define ``ansible_become_pass`` or set
``ansible_become_pass: ''``.

Before become can work on an account like this, the local policy
`Accounts: Limit local account use of blank passwords to console logon only <https://technet.microsoft.com/en-us/library/jj852174.aspx>`_
must be disabled. This can either be done through a Group Policy Object (GPO)
or with this Ansible task:

.. code-block:: yaml

   - name: allow blank password on become
     win_regedit:
       path: HKLM:\SYSTEM\CurrentControlSet\Control\Lsa
       name: LimitBlankPasswordUse
       data: 0
       type: dword
       state: present

.. Note:: This is only for accounts that do not have a password. You still need
    to set the account's password under ``ansible_become_pass`` if the
    become_user has a password.

Become Flags
------------
Ansible 2.5 adds the ``become_flags`` parameter to the ``runas`` become method.
This parameter can be set using the ``become_flags`` task directive or set in
Ansible's configuration using ``ansible_become_flags``. The two valid values
that are initially supported for this parameter are ``logon_type`` and
``logon_flags``.


.. Note:: These flags should only be set when becoming a normal user account, not a local service account like LocalSystem.

The key ``logon_type`` sets the type of logon operation to perform. The value
can be set to one of the following:

* ``interactive``: The default logon type. The process will be run under a
  context that is the same as when running a process locally. This bypasses all
  WinRM restrictions and is the recommended method to use.

* ``batch``: Runs the process under a batch context that is similar to a
  scheduled task with a password set. This should bypass most WinRM
  restrictions and is useful if the ``become_user`` is not allowed to log on
  interactively.

* ``new_credentials``: Runs under the same credentials as the calling user, but
  outbound connections are run under the context of the ``become_user`` and
  ``become_password``, similar to ``runas.exe /netonly``. The ``logon_flags``
  flag should also be set to ``netcredentials_only``. Use this flag if
  the process needs to access a network resource (like an SMB share) using a
  different set of credentials.

* ``network``: Runs the process under a network context without any cached
  credentials. This results in the same type of logon session as running a
  normal WinRM process without credential delegation, and operates under the same
  restrictions.

* ``network_cleartext``: Like the ``network`` logon type, but instead caches
  the credentials so it can access network resources. This is the same type of
  logon session as running a normal WinRM process with credential delegation.

For more information, see
`dwLogonType <https://msdn.microsoft.com/en-au/library/windows/desktop/aa378184.aspx>`_.

The ``logon_flags`` key specifies how Windows will log the user on when creating
the new process. The value can be set to none or multiple of the following:

* ``with_profile``: The default logon flag set. The process will load the
  user's profile in the ``HKEY_USERS`` registry key to ``HKEY_CURRENT_USER``.

* ``netcredentials_only``: The process will use the same token as the caller
  but will use the ``become_user`` and ``become_password`` when accessing a remote
  resource. This is useful in inter-domain scenarios where there is no trust
  relationship, and should be used with the ``new_credentials`` ``logon_type``.

By default ``logon_flags=with_profile`` is set, if the profile should not be
loaded set ``logon_flags=`` or if the profile should be loaded with
``netcredentials_only``, set ``logon_flags=with_profile,netcredentials_only``.

For more information, see `dwLogonFlags <https://msdn.microsoft.com/en-us/library/windows/desktop/ms682434.aspx>`_.

Here are some examples of how to use ``become_flags`` with Windows tasks:

.. code-block:: yaml

  - name: copy a file from a fileshare with custom credentials
    win_copy:
      src: \\server\share\data\file.txt
      dest: C:\temp\file.txt
      remote_src: yex
    vars:
      ansible_become: yes
      ansible_become_method: runas
      ansible_become_user: DOMAIN\user
      ansible_become_pass: Password01
      ansible_become_flags: logon_type=new_credentials logon_flags=netcredentials_only

  - name: run a command under a batch logon
    win_whoami:
    become: yes
    become_flags: logon_type=batch

  - name: run a command and not load the user profile
    win_whomai:
    become: yes
    become_flags: logon_flags=


Limitations
-----------

Be aware of the following limitations with ``become`` on Windows:

* Running a task with ``async`` and ``become`` on Windows Server 2008, 2008 R2
  and Windows 7 does not work.

* By default, the become user logs on with an interactive session, so it must
  have the right to do so on the Windows host. If it does not inherit the
  ``SeAllowLogOnLocally`` privilege or inherits the ``SeDenyLogOnLocally``
  privilege, the become process will fail. Either add the privilege or set the
  ``logon_type`` flag to change the logon type used.

* Prior to Ansible version 2.3, become only worked when
  ``ansible_winrm_transport`` was either ``basic`` or ``credssp``. This
  restriction has been lifted since the 2.4 release of Ansible for all hosts
  except Windows Server 2008 (non R2 version).

.. seealso::

   `Mailing List <https://groups.google.com/forum/#!forum/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `webchat.freenode.net <https://webchat.freenode.net>`_
       #ansible IRC chat channel

