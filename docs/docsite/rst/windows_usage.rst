Using Ansible and Windows
=========================
When using Ansible to manage Windows, a lot of the syntax and rules that apply
for Unix/Linux hosts also apply to Windows. There are still some differences
between the hosts when it comes to components like path separators and OS
specific tasks. Details specific for Windows such as how to install programs,
represent paths in YAML can be found on this page.

.. contents:: Topics

Use Cases
`````````
Ansible can be used to orchestrate a multitude of tasks on Windows servers,
below are some examples and info about common tasks.

Installing Programs
-------------------
There are three main ways that Ansible can be used to install programs which
are:

* Using the ``win_chocolatey`` module sources the program data from an external
  chocolatey repository. Internal repositories can be used instead by setting
  the ``source`` option. 

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

Some installers restart the WinRM service, or cause it to become (temporarily)
unavaible, making Ansible assume the system is unreachable.

Installing Updates
------------------
The modules ``win_updates`` and ``win_hotfix`` can be used to install updates
or hotfixes on a host. The module ``win_updates`` is used to install multiple
updates per a category while ``win_hotfix`` can be used to install a single
update or hotfix file that has been downloaded locally.

.. Note:: ``win_hotfix`` has a requirement on the DISM PowerShell cmdlets being
    present. These cmdlets were only added by default on Windows Server 2012
    and newer and must be installed on older Windows hosts.

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
In the case that there is no module that can complete a task that is required,
a command or script can be run using the ``win_shell``/``win_command``/``raw``/
``script`` modules. 

The ``raw`` module executes a low level command without any of the normal
wrappers that Ansible uses. Because of this, things like ``become``, ``async``
and environment variables do not work and ``raw`` should be not be used unless
required.

The ``script`` module executes a script from a local directory to the Ansible
host on the Windows server. Like ``raw`` is currently does not support
``become``, ``async`` and environment variables. It still has its uses if the
script to be executed is located on the Ansible host and not the Windows host.

The ``win_command`` module is used to execute a command which is either an
executable or batch file while ``win_shell`` is used to execute command(s)
within a shell. Further down has more details on the differences between the
two.

Command or Shell
++++++++++++++++
The modules ``win_shell`` and ``win_command`` are similar in the fact that they
can be used to execute a command or commands. ``win_shell`` is run within a
shell like process like ``PowerShell`` or ``cmd`` so it has access to shell
operators like ``<``, ``>``, ``|``, ``;``, ``&&``, ``||`` and so on.
Multi-lined commands can also be run in ``win_shell``.

``win_command`` is different where it is meant to run an executable outside of
a shell. It can still run a shell command like ``mkdir``, ``New-Item`` by
running it with the ``cmd.exe`` or ``PowerShell.exe`` executable.

Here are some examples of using ``win_command`` or ``win_shell``::

    - name: run a command under PowerShell
      win_shell: Get-Service -Name service | Stop-Service
    
    - name: run a command under cmd
      win_shell: mkdir C:\temp
      args:
        executable: cmd.exe
    
    - name: run a multiple shell commands
      win_shell: |
        New-Item -Path C:\temp -ItemType Directory
        Remove-Item -Path C:\temp -Force -Recurse
        $path_info = Get-Item -Path C:\temp
        $path_info.FullName
    
    - name: run an executable using win_command
      win_command: whoami.exe
    
    - name: run a cmd command
      win_command: cmd.exe /c mkdir C:\temp

    - name: run a vbs script
      win_command: cscript.exe script.vbs

.. Note:: Some commands like ``mkdir``, ``del``, ``copy`` are all commands that
    only exist in the CMD shell. To run them with ``win_command`` they must be
    prefixed with ``cmd.exe /c``.

Argument Rules
++++++++++++++
When running a command through ``win_command``, the standard Windows argument
rules apply. 

The rules can be simplified to the following points:

* Each argument is delimited by a white space, which can either be a space or a
  tab

* An argument can be surrounded by double quotes ``"``, anything inside these
  quotes is interpreted as a single argument even if it contains whitespace

* A double quote preceded by a backslash ``\`` is interpreted as just a double
  quote ``"`` not as an argument delimiter

* Backslashes are interpreted literally unless it is immediately preceeds double
  quotes, e.g. ``\`` == ``\`` and ``\"`` == ``"``

* If an even number of backslashes is followed by a double quote, one
  backslash is used in the argument for every pair and the double quote is
  used as a string delimiter for the argument

* If an odd number of backslashes is followed by a double quote, one backslash
  is used in the argument for every pair and the double quote is escaped and
  made a literal double quote in the argument

Using the following rules, these are some examples of quoting::

    - win_command: C:\temp\executable.exe argument1 "argument 2" "C:\path\with space" "double \"quoted\""

    argv[0] = C:\temp\executable.exe
    argv[1] = argument1
    argv[2] = argument 2
    argv[3] = C:\path\with space
    argv[4] = double "quoted"

    - win_command: '"C:\Program Files\Program\program.exe" "escaped \\\" backslash" unqouted-end-backslash\'

    argv[0] = C:\Program Files\Program\program.exe
    argv[1] = escaped \" backslash
    argv[2] = unquoted-end-backslash\

    # due to YAML and Ansible parsing '\"' must be written as '{% raw %}\\{% endraw %}"'
    - win_command: C:\temp\executable.exe C:\no\space\path "arg with end \ before end quote{% raw %]\\{% endraw %}"

    argv[0] = C:\temp\executable.exe
    argv[1] = C:\no\space\path
    argv[2] = arg with end \ before end quote\"

These rules can be further explored in greater depth by reading
`escaping arguments <https://msdn.microsoft.com/en-us/library/17w5ykft(v=vs.85).aspx>`_.

Creating and Running Scheduled Task
-----------------------------------
As WinRM has a few restrictions in place that cause errors when running certain
commands, one way to bypass these restrictions is to run a command through a
scheduled task. Scheduled tasks is a Windows component that provides the
ability to run an executable on a schedule and under a different account.

As of Ansible 2.5, the modules used to manipulate scheduled tasks have made it
easier to create an adhoc task, run it and wait for completion. The following
is an example of running a script as a scheduled task that deletes itself after
running::

    - name: create scheduled task to run a process
      win_scheduled_task:
        name: adhoc-task
        username: SYSTEM
        actions:
        - path: PowerShell.exe
          arguments: |
            Start-Sleep -Seconds 30 # this isn't required, just here as a demonstration
            New-Item -Path C:\temp\test -ItemType Directory
        # remove this action if the task shouldn't be deleted on completion
        - path: cmd.exe
          arguments: /c schtasks.exe /Delete /TN "adhoc-task" /F
        triggers:
        - type: registration

    - name: wait for the scheduled task to complete
      win_scheduled_task_stat:
        name: adhoc-task
      register: task_stat
      until: (task_stat.state is defined and task_stat.state.status != "TASK_STATE_RUNNING") or (task_stat.task_exists == False)
      retries: 12
      delay: 10

.. Note:: The modules used in the above example were updated/added in Anisble
    2.5. While older versions can do this, this example will not work.

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

The YAML specification considers the following `escape sequences <http://www.yaml.org/spec/current.html#id2517668>`_:

* ``\0``, ``\``, ``"``, ``\a``, ``\b``, ``\e``, ``\f``, ``\n``, ``\r``, ``\t``
  and ``\v`` -- Single character escape

* ``<TAB>``, ``<SPACE>``, ``<NBSP>``, ``<LNSP>``, ``<PSP>`` -- Special
  characters

* ``\x..`` -- 2-digit hex escape

* ``\u....`` -- 4-digit hex escape

* ``\U........`` -- 8-digit hex escape

Here are some examples on how to write Windows paths::

    GOOD
    tempdir: C:\Windows\Temp

    WORKS
    tempdir: 'C:\Windows\Temp'
    tempdir: "C:\\Windows\\Temp"

    BAD, BUT SOMETIMES WORKS
    tempdir: C:\\Windows\\Temp
    tempdir: 'C:\\Windows\\Temp'
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
or inside playbooks. The use of this style is discouraged within playbooks
because backslash need to be escaped and it makes playbooks harder to read.
This syntax depends on the specific implementation in Ansible, and quoting
(both single and double) does not have any effect on how it is parsed by
Ansible.

The Ansible key=value parser parse_kv() considers the following escape
sequences:

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

Limitations
```````````
Some things you cannot do, or do easily, with Ansible are:

* Upgrade PowerShell

* Interact with the WinRM listeners

This is because WinRM is reliant on the services being online and running
during normal operations. If PowerShell was to be upgraded or the WinRM service
was bounced then the connection will fail. This can technically be avoided
by using ``async`` or a scheduled task but those methods are fragile if the
process it runs breaks the underlying connection Ansible uses.

These steps are best left to the bootstrapping process or before an image is
created.

Developing Windows Modules
``````````````````````````
Because Ansible modules for Windows are written in PowerShell, the development
guides differ from the usual practice. Please see
:doc:`dev_guide/developing_modules_general_windows` for more information about
this topic.

.. seealso::

   :doc:`index`
       The documentation index
   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_best_practices`
       Best practices advice
   `List of Windows Modules <http://docs.ansible.com/list_of_windows_modules.html>`_
       Windows specific module list, all implemented in PowerShell
   `User Mailing List <http://groups.google.com/group/ansible-project>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
