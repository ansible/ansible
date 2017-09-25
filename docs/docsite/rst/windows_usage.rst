Using Ansible and Windows
=========================
Info about using Ansible and Windows such as common use cases and how to write
tasks.

Use Cases
`````````
Some common use cases with Ansible and Windows.

Installing Programs
-------------------
There are three main ways that Ansible can be used to install programs which
are:

* Using the ``win_chocolatey`` module which installs by default from an
  external chocolatey repository

* Using the ``win_package`` module which installs a program from a
  local/network path or URL

* Using the ``win_command`` or ``win_shell`` module to install it manually

It is recommended to use the ``win_chocolatey`` module as all the logic to
check if it is already installed and how to install it is done by Chocolatey.

Here are some examples of installing 7-Zip with all three options::

    # install/uninstall with chocolatey
    - name: ensure 7-Zip is installed using Chocolatey
      win_chocolatey:
        name: 7zip
        state: present
    
    - name: ensure 7-Zip is uninstall using Chocolatey
      win_chocolatey:
        name: 7zip
        state: absent
    
    # install/uninstall with win_package
    - name: download the 7-Zip package
      win_get_url:
        url: http://www.7-zip.org/a/7z1701-x64.msi
        dest: C:\temp\7z.msi

    - name: ensure 7-Zip is installed using win_package
      win_package:
        path: C:\temp\7z.msi
        state: present
    
    - name: ensure 7-Zip is uninstall using win_package
      win_package:
        path: C:\temp\7z.msi
        state: absent

    # install/uninstall with win_command
    - name: download the 7-Zip package
      win_get_url:
        url: http://www.7-zip.org/a/7z1701-x64.msi
        dest: C:\temp\7z.msi
    
    - name: check if 7-Zip is already installed
      win_reg_stat:
        name: HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{23170F69-40C1-2702-1701-000001000000}
      register: 7zip_installed
    
    - name: ensure 7-Zip is installed using win_command
      win_command: C:\Windows\System32\msiexec.exe /i C:\temp\7z.msi /qn /norestart
      when: 7zip_installed.exists == False
    
    - name: ensure 7-Zip is uninstalled using win_command
      win_command: C:\Windows\System32\msiexec.exe /x {23170F69-40C1-2702-1701-000001000000} /qn /norestart
      when: 7zip_installed.exists == True

Some progam installers like Office, SQL Server require credential delegation or
access to components restricted by WinRM. The best method to bypass these
issues is to use ``become`` with the task. With ``become``, Ansible will run
the module like it would when running it locally. Unfortunately a lot of the
installers are vague when it errors out over WinRM, the best bet is if it works
locally and not through Ansible is to use become.

Installing Updates
------------------
The modules ``win_updates`` and ``win_hotfix`` can be used to install updates
or hotfixes on a host. The module ``win_updates`` is used to install multiple
updates per a category while ``win_hotfix`` can be used to install a single
update or hotfix file that has been downloaded locally.

.. Note:: ``win_hotfix`` has a requirement on the DISM powershell cmdlets being
    present. These cmdlets were only added by default on Windows Server 2012
    and newer.

The following example shows how ``win_updates`` can be used::

    - name: install all critical and security updates
      win_updates:
        category_names:
        - CriticalUpdates
        - SecurityUpdates
        state: installed
      register: update_result
    
    - name: reboot host if required
      win_reboot:
      when: update_result.reboot_required

The following example show how ``win_hotfix`` can be used to install a single
update or hotfix::

    - name: download KB3172729 for Server 2012 R2
      win_get_url:
        url: http://download.windowsupdate.com/d/msdownload/update/software/secu/2016/07/windows8.1-kb3172729-x64_e8003822a7ef4705cbb65623b72fd3cec73fe222.msu
        dest: C:\temp\KB3172729.msu
    
    - name: install hotfix
      win_hotfix:
        hotfix_kb: KB3172729
        source: C:\temp\KB3172729.msu
        state: present
      register: hotfix_result
    
    - name: reboot host if required
      win_reboot:
      when: hotfix_result.reboot_required

Setup Users and Groups
----------------------
Ansible can be used to create users and groups both locally and on a domain.

Local
+++++
The modules ``win_user``, ``win_group`` and ``win_group_membership`` manages
users, groups and group memberships locally.

The following is an example of creating local accounts and groups that can
access a folder locally::

    - name: create local group users will be members of
      win_group:
        name: LocalGroup
        description: Allow access to C:\Development folder

    - name: create local user
      win_user:
        name: '{{item.name}}'
        password: '{{item.password}}'
        groups: LocalGroup
        update_password: no
        password_never_expired: yes
      with_items:
      - name: User1
        password: Password1
      - name: User2
        password: Password2
    
    - name: create Development folder
      win_file:
        path: C:\Development
        state: directory
    
    - name: set ACL of Development folder
      win_acl:
        path: C:\Development
        rights: FullControl
        state: present
        type: allow
        user: LocalGroup
    
    - name: remove parent inheritance of Development folder
      win_acl_inheritance:
        path: C:\Development
        reorganize: yes
        state: absent

Domain
++++++
The modules ``win_domain_user`` and ``win_domain_group`` manages users and
groups in a domain. The below is an example of ensuring a batch of domain users
are created::

    - name: ensure each account is created
      win_domain_user:
        name: '{{item.name}}'
        upn: '{{item.name}}@MY.DOMAIN.COM'
        password: '{{item.password}}'
        password_never_expires: no
        groups:
        - Test User
        - Application
        company: Ansible
        update_password: on_create
      with_items:
      - name: Test User
        password: Password
      - name: Admin User
        password: SuperSecretPass01
      - name: Dev User
        password: '@fvr3IbFBujSRh!3hBg%wgFucD8^x8W5'

Running Commands
----------------
Info on running a command/process using ``win_shell``/``win_command``/``raw``/``script``.

Escaping Spaces
+++++++++++++++

Command or Shell
++++++++++++++++

Creating and Running Scheduled Task
-----------------------------------
Info on how to create a scheduled task, run and wait for it to compelete.

Path Formatting for Windows
```````````````````````````
Windows is unlike a traditional POSIX operating system in many ways but one of
the major changes is the shift from ``/`` as the path separator to ``\``. This
can cause major issues with how playbooks are written as ``\`` can be seen as
an escape character in certain situations.

There are two ways of writting tasks in Ansible and each way have their own
recommended way of dealing with path separators for Windows.

YAML Style
----------
When using the YAML syntac for tasks, the rules are well-defined by the YAML
standard:

* When using normal string (without quotes), YAML will not consider the
  backslash an escape character

* When using single quotes ``'``, YAML will not consider the backslash an
  escape character

* When using double quotes ``"``, the backslash is considered an escape
  character and need to escaped with another backslash

.. Note:: It is recommended to only quote strings when it is absolutely
    necessary or required by YAML and if quotes are required, use single quotes

The YAML specification considers the following escape sequences_:

* ``\0``, ``\``, ``"``, ``\a``, ``\b``, ``\e``, ``\f``, ``\n``, ``\r``, ``\t``
  and ``\v`` -- Single character escape

* ``<TAB>``, ``<SPACE>``, ``<NBSP>``, ``<LNSP>``, ``<PSP>` -- Special
  characters

* ``\x..`` -- 2-digit hex escape

* ``\u....`` -- 4-digit hex escape

* ``\U........`` -- 8-digit hex escape

.. _escape sequences: http://www.yaml.org/spec/current.html#id2517668

Here are some examples on how to write Windows paths::

    GOOD
    tempdir: C:\Windows\Temp

    WORKS
    tempdir: 'C:\Windows\Temp'
    tempdir: "C:\\Windows\\Temp"

    BAD, BUT SOMETIMES WORKS
    tempdir: C:\\Windows\\Temp
    tempdir: 'C:\\Windows\\Temp
    tempdir: C:/Windows/Temp

    FAILS
    tempdir: "C:\Windows\Temp"

    ---
    # example of single quotes when they are required
    - name: copy tomcat config
      win_copy:
        src: log4j.xml
        dest: '{{tc_home}}\lib\log4j.xml'

Legacy key=value Style
----------------------
The legacy ``key=value`` syntax is used on the command line for adhoc commands,
or inside playbook. Using this style is not recommended for using inside
playbooks as backslashes need to escaped and it makes the tasks harder to read.
This syntact depends on the specific implementation in Ansible, and quoting
(both single and double) does not have any effect on how it is parsed by
Ansible.

The Ansible key=value parser parse_kv() considers the following escape
sequences::

* ``\``, ``'``, ``"``, ``\a``, ``\b``, ``\f``, ``\n``, ``\r``, ``\t`` and
  ``\v`` -- Single character escape

* ``\x..`` -- 2-digit hex escape

* ``\u....`` -- 4-digit hex escape

* ``\U........`` -- 8-digit hex escape

* ``\N{...}`` -- Unicode character by name

This means that the backslash is an escape character for some sequences, and it
is usually safer to escape a backslash when in this form.

Here are some examples of using Windows paths with the key=value style::

    GOOD
    tempdir=C:\\Windows\\Temp

    WORKS
    tempdir='C:\\Windows\\Temp'
    tempdir="C:\\Windows\\Temp"

    BAD, BUT SOMETIMES WORKS
    tempdir=C:\Windows\Temp
    tempdir='C:\Windows\Temp'
    tempdir="C:\Windows\Temp"
    tempdir=C:/Windows/Temp

    FAILS
    tempdir=C:\Windows\temp
    tempdir='C:\Windows\temp'
    tempdir="C:\Windows\temp"

The failing examples don't fail outright but will substitute ``\t`` with the
``<TAB>`` character resulting in ``tempdir`` being ``C:\Windows<TAB>emp``.

What you Cannot Do
``````````````````
Some things you cannot do, or do easily, with Ansible are:

* Upgrade powershell

* Interact with the WinRM listeners

This is because WinRM is reliant on the services being online and running
during normal operations. If powershell was to be upgraded or the WinRM service
was to bounced then the connection will fail. This can technically be avoided
by using ``async`` or a scheduled task but those methods are fragile if the
process it runs breaks the underlying connection Ansible uses.

These steps are best left to the bootstrapping process or before an image is
created.
