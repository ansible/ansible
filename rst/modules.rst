Ansible Modules
===============

Ansible ships with a number of modules (called the 'module library') 
that can be executed directly on remote hosts or through :doc:`playbooks`.
Users can also write their own modules.   These modules can control system
resources, like services, packages, or files (anything really), or 
handle executing system commands.  

Let's review how we execute three different modules from the command line::

    ansible webservers -m service -a "name=httpd state=running"
    ansible webservers -m ping
    ansible webservers -m command -a "/sbin/reboot -t now"

Each module supports taking arguments.  Nearly all modules take ``key=value`` 
arguments, space delimited.  Some modules take
no arguments, and the command/shell modules simply take the string
of the command you want to run.

From playbooks, Ansible modules are executed in a very similar way::

    - name: reboot the servers
      action: command /sbin/reboot -t now 

All modules technically return JSON format data, though if you are using the
command line or playbooks, you don't really need to know much about
that.  If you're writing your own module, you care, and this means you do
not have to write modules in any particular language -- you get to choose.

Most modules other than command are `idempotent`, meaning they will seek
to avoid changes to the system unless a change needs to be made.  When using Ansible
playbooks, these modules can trigger 'change events'.  Unless otherwise
noted, any given module does support change hooks.

Let's see what's available in the Ansible module library, out of the box:

.. _apt:

apt
```

Manages apt-packages (such as for Debian/Ubuntu).

*pkg*:

* A package name or package specifier with version, like `foo`, or `foo=1.0` to
install a specific version of the foo package.

*state*:

* Can be either 'installed', 'removed', or 'latest'.  The default is 'installed'.  (In 0.4 and later, the aliases 'absent' and 'present' can also be used.  They correspond with 'removed' and 'installed')

*update-cache*:

* Whether the apt cache must be updated prior to operation. Optional, and can be
  'yes', or 'no'. The default is 'no'.  This can be done as the part of a
  package operation or as a seperate step.

*purge*:

* Will force purge of configuration file for when ensure is set to 'removed'.
  Defaults to 'no'.

*default-release*:

* Corresponds to the -t option for apt, and sets pin priorities

Example action from Ansible :doc:`playbooks`::

    apt pkg=foo update-cache=yes
    apt pkg=foo state=removed
    apt pkg=foo state=installed
    apt pkg=foo=1.00 state=installed
    apt pkg=nginx state=latest default-release=squeeze-backports update-cache=yes


NOTE: the apt module cannot currently request installation of a specific software version, as the yum
module can.  This should be available in a future release.

.. _command:

command
```````

The command module takes the command name followed by a list of
arguments, space delimited.  

If you want to run a command through the shell (say you are using
'<', '>', '|', etc), you actually want the 'shell' module instead.  
The 'command' module is much more secure as it's not affected by the user's environment.

The given command will be executed on all selected nodes.  It will not
be processed through the shell, so variables like "$HOME" and 
operations like "<", ">", "|", and "&" will not work.  As such, all
paths to commands must be fully qualified.

This module does not support change hooks and returns the return code
from the program as well as timing information about how long the
command was running.

Example action from Ansible :doc:`playbooks`::

    command /sbin/shutdown -t now

If you only want to run a command if a certain file does not exist, you can do the
following::

    command /usr/bin/make_database.sh arg1 arg2 creates=/path/to/database

The `creates=` option will not be passed to the executable.


.. _copy:

copy
````

The copy module moves a file on the local box to remote locations.  In addition to the options
listed below, the arguments available to the `file` module can also be passed to the copy
module.

*src*:

* Local path to a file to copy to the remote server.  This can be an
  absolute or relative path.


*dest*:

* Remote absolute path where the file should end up.

This module also returns md5sum information about the resultant file.

Example action from Ansible :doc:`playbooks`::

    copy src=/srv/myfiles/foo.conf dest=/etc/foo.conf owner=foo group=foo mode=0644


.. _facter:

facter
``````

Runs the discovery program 'facter' on the remote system, returning
JSON data that can be useful for inventory purposes.  

Requires that 'facter' and 'ruby-json' be installed on the remote end.

This module is informative only - it takes no parameters & does not
support change hooks, nor does it make any changes on the system.
Playbooks do not actually use this module, they use the :ref:`setup`
module behind the scenes.


fetch
`````

This module works like 'copy', but in reverse.  It is used for fetching files
from remote machines and storing them locally in a file tree, organized by hostname.

*src*:

* The file on the remote system to fetch.  This needs to be a file, not a directory. Recursive fetching may be supported later.

*dest*:

* A directory to save the file into.  For example, if the 'dest' directory is '/foo', a src file named '/tmp/bar' on host 'host.example.com', would be saved into '/foo/host.example.com/tmp/bar' (in Ansible 0.0.3 and later).

The fetch module is a useful way to gather log files from remote systems.  If you require
fetching multiple files from remote systems, you may wish to execute a tar command and
then fetch the tarball.

Example::

    fetch src=/var/log/messages dest=/home/logtree


file
````

Sets attributes of files, symlinks, and directories, or removes files/symlinks/directories. 
All parameters available to the file module are also available when running the `copy` or 
`template` modules.

*dest*:

* alias for 'path'. Sets an absolute path to a file on the filesystem when used with 'state=file'. When used with 'state=link', sets the destination to create a symbolic link defined by 'src' key.

*state*:

* either 'file', 'link', 'directory', or 'absent'.  The default is 'file'.  If 'directory', the directory and all immediate subdirectories will be created if they do not exist.  If 'file', the file will NOT be created if it does not exist, specify `copy` or `template` for the module name instead if you need to put content at the specified location.  If 'link', the symbolic link will be created or changed.  If 'absent', directories will be recursively deleted, and files or symlinks will be unlinked.

*mode*:

* the mode the file or directory should be, such as 644, as would be given to `chmod`.  English modes like "g+x" are not yet supported.

*owner*:

* name of user that should own the file or directory, as would be given to `chown`

*group*:

* name of group that should own the file or directory, as would be given to `chgrp`

*src*:

* path of the file to link to (applies only to 'link' state)

*seuser*:

* 'user' part of SELinux file context.  Will default to what is provided by system policy, if available.  Only used on systems with SELinux present.  If you specify '_default', it will use the 'user' portion of default context from the policy if available.

*serole*:

* 'role' part of SELinux file context.  Will default to what is provided by system policy, if available.  Only used on systems with SELinux present.  If you specify '_default', it will use the 'role' portion of default context from the policy if available.

*setype*:

* 'type' part of SELinux file context.  Will default to what is provided by system policy, if available.  Only used on systems with SELinux present.  If you specify '_default', it will use the 'type' portion of default context from the policy if available.

*selevel*:

* 'level' part of SELinux file context.  This is the MLS and MCS attribute of the file context, also sometimes known as the 'range'.  It defaults to 's0'.  Only used only used on hosts with SELinux present.  If you specify '_default', it will use the 'level' portion of default context from the policy if available.

*context*:

* accepts only 'default' as value.  This will restore a file's selinux context to the default context in the policy.  Does nothing if no default is available. Only used on hosts with SELinux present.

Example action from Ansible :doc:`playbooks`::

    file path=/etc/foo.conf owner=foo group=foo mode=0644
    file path=/some/path owner=foo group=foo state=directory
    file path=/path/to/delete state=absent
    file src=/file/to/link/to dest=/path/to/symlink owner=foo group=foo state=link
    file path=/some/path state=directory setype=httpd_sys_content_t
    file path=/some/path state=directory context=default

.. _git:

git
```

Deploys software (or files) from git checkouts.

*repo*:

* git, ssh, or http protocol address of the git repo to checkout.

*dest*:

* Where to check it out, an absolute directory path.

*version*:

* What version to check out -- either the git SHA, the literal string
  ``HEAD``, or a tag name.

*branch*:

* (new in 0.4) Which branch name to checkout.  Defaults to 'master'.

Example action from Ansible :doc:`playbooks`::

    git repo=git://foosball.example.org/path/to/repo.git dest=/srv/checkout version=release-0.22

.. _group:

group
`````

Adds or removes groups.

*name*:

* name of the group

*gid*:

* optional gid to set for the group

*state*:

* either 'absent', or 'present'.  'present' is the default.

*system*:

* (new in 0.4) Indicates the group (when being created), should be a system group.  This does not allow changing groups from and to system groups.  Value is 'yes' or 'no', default is 'no'.


To control members of the group, see the users resource.

Example action from Ansible :doc:`playbooks`::

   group name=somegroup state=present

.. _ohai:

ohai
````

Similar to the :ref:`facter` module, this returns JSON inventory data.
Ohai data is a bit more verbose and nested than facter.

Requires that 'ohai' be installed on the remote end.

This module is information only - it takes no parameters & does not
support change hooks, nor does it make any changes on the system.

Playbooks should not call the ohai module, playbooks call the
:ref:`setup` module behind the scenes instead.

.. _ping:

ping
````

A trivial test module, this module always returns the integer ``1`` on
successful contact.

This module does not support change hooks and is informative only - it
takes no parameters & does not support change hooks, nor does it make
any changes on the system.

.. _service:

raw
```

Executes a low-down and dirty SSH command, not going through the module subsystem.
This module is new in Ansible 0.4.

This is useful and should only be done in two cases.  The first case is installing
python-simplejson on older (python 2.4 and before) hosts that need it as a dependency
to run modules, since nearly all core modules require it.  Another is speaking to any 
devices such as routers that do not have any Python installed.  In any other case,
using the 'shell' or 'command' module is much more appropriate.

Arguments given to 'raw' are run directly through the configured remote shell and 
only output is returned.  There is no error detection or change handler support 
for this module.

Example from `/usr/bin/ansible` to bootstrap a legacy python 2.4 host:

    ansible newhost.example.com raw -a "yum install python-simplejson"

service
```````

Controls services on remote machines.

*state*:

* Values are ``started``, ``stopped``, or ``restarted``.
  Started/stopped are idempotent actions that will not run commands
  unless necessary.  ``restarted`` will always bounce the service.

*enabled*:

* (new in 0.4) Whether the service should start on boot.  Either 'yes' or 'no'.
  Uses chkconfig or updates-rc.d as appropriate.

*list*:

* (new in 0.4) When used with the value 'status', returns the status of the service along with other results.  This is primarily useful for /usr/bin/ansible, and not meaningful for playbooks.

*name*:

* The name of the service.

Example action from Ansible :doc:`playbooks`::

    service name=httpd state=started
    service name=httpd state=stopped
    service name=httpd state=restarted

.. _setup:

setup
`````

Writes a JSON file containing key/value data, for use in templating.
Call this once before using the :ref:`template` module.  Playbooks
will execute this module automatically as the first step in each play
using the variables section, so it is unnecessary to make explicit
calls to setup within a playbook.

Ansible provides many 'facts' about the system, automatically.

Some of the variables that are supplied are listed below.  These in particular
are from a VMWare Fusion 4 VM running CentOS 6.2::

    "ansible_architecture": "x86_64",
    "ansible_distribution": "CentOS",
    "ansible_distribution_release": "Final",
    "ansible_distribution_version": "6.2",
    "ansible_eth0": {
        "ipv4": {
            "address": "REDACTED",
            "netmask": "255.255.255.0"
        },
        "ipv6": [
            {
                "address": "REDACTED",
                "prefix": "64",
                "scope": "link"
            }
        ],
        "macaddress": "REDACTED"
    },
    "ansible_form_factor": "Other",
    "ansible_fqdn": "localhost.localdomain",
    "ansible_hostname": "localhost",
    "ansible_interfaces": [
        "lo",
        "eth0"
    ],
    "ansible_kernel": "2.6.32-220.2.1.el6.x86_64",
    "ansible_lo": {
        "ipv4": {
            "address": "127.0.0.1",
            "netmask": "255.0.0.0"
        },
        "ipv6": [
            {
                "address": "::1",
                "prefix": "128",
                "scope": "host"
            }
        ],
    "ansible_machine": "x86_64",
    "ansible_memfree_mb": 89,
    "ansible_memtotal_mb": 993,
    "ansible_processor": [
        "Intel(R) Core(TM) i7-2677M CPU @ 1.80GHz"
    ],
    "ansible_processor_cores": "NA",
    "ansible_processor_count": 1,
    "ansible_product_name": "VMware Virtual Platform",
    "ansible_product_serial": "REDACTED",
    "ansible_product_uuid": "REDACTED",
    "ansible_product_version": "None",
    "ansible_python_version": "2.6.6",
    "ansible_product_version": "None",
    "ansible_python_version": "2.6.6",
    "ansible_ssh_host_key_dsa_public": REDACTED",
    "ansible_ssh_host_key_rsa_public": "REDACTED",
    "ansible_swapfree_mb": 1822,
    "ansible_swaptotal_mb": 2015,
    "ansible_system": "Linux",
    "ansible_system_vendor": "VMware, Inc.",
    "ansible_virtualization_role": "None",
    "ansible_virtualization_type": "None",

More ansible facts will be added with successive releases.

If facter or ohai are installed, variables from these programs will
also be snapshotted into the JSON file for usage in templating. These
variables are prefixed with ``facter_`` and ``ohai_`` so it's easy to
tell their source.  

All variables are bubbled up to the caller.  Using the ansible facts and choosing
to not install facter and ohai means you can avoid ruby-dependencies
on your remote systems.

*variablename*:

* Arbitrary variable names, which must be a mix of alphanumeric characters and underscores, can also be defined. Setting a variable creates a ``key=value`` pair in the JSON file for use in templating.

Example action from Ansible :doc:`playbooks`::

    vars:
        ntpserver: 'ntp.example.com'
        xyz: 1234

Example action from `/usr/bin/ansible`::

    ansible all -m setup -a "ntpserver=ntp.example.com xyz=1234"


.. _shell:

shell
`````

The shell module takes the command name followed by a list of
arguments, space delimited.  It is almost exactly like the command module
but runs the command through the user's configured shell on the remote node.

The given command will be executed on all selected nodes.  

If you want to execute a command securely and predicably, it may
be better to use the 'command' module instead.  Best practices
when writing playbooks will follow the trend of using 'command'
unless 'shell' is explicitly required.  When running ad-hoc commands,
use your best judgement.

This module does not support change hooks and returns the return code
from the program as well as timing information about how long the
command was running.

Example action from a playbook::

    shell somescript.sh >> somelog.txt


.. _template:

template
````````

Templates a file out to a remote server.  Call the :ref:`setup` module
prior to usage if you are not running from a playbook.   In addition to the options
listed below, the arguments available to the `file` and `copy` modules can also be passed
to the template module.

*src*:

* Path of a Jinja2 formatted template on the local server.  This can
  be a relative or absolute path.

*dest*:

* Location to render the template on the remote server

This module also returns md5sum information about the resultant file.

Example action from a playbook::

    template src=/srv/mytemplates/foo.j2 dest=/etc/foo.conf owner=foo group=foo mode=0644


.. _user:

user
````

Creates user accounts, manipulates existing user accounts, and removes user accounts.

*name*:

* Name of the user to create, remove, or edit

*comment*:

* Optionally sets the description of the user

*uid*:

* optional uid to set for the user

*group*:

* Optionally sets the user's primary group, takes a group name

*groups*:

* Put the user in the specified groups, takes comma delimited group names

*append*:

* If true, will only add additional groups to the user listed in 'groups', rather than making the user only be in those specified groups

*shell*:

* Optionally sets the user's shell

*createhome*:

* Whether to create the user's home directory.  Takes 'yes', or 'no'.  The default is 'yes'.
    
*password*:

* Sets the user's password to this crypted value.  Pass in a result from crypt.  See the users example in the github examples directory for what this looks like in a playbook.

*state*:

* Defaults to 'present'.  When 'absent', the user account will be removed if present.  Optionally additional removal behaviors can be set with the 'force' or 'remove' parameter values (see below).

*system*:

* (new in 0.4) Indicates the user (when being created), should be a system account.  This does not allow changing users from and to system accounts.  Value is 'yes' or 'no', default is 'no'.

*force*:

* When used with a state of 'absent', the behavior denoted in the 'userdel' manpage for ``--force`` is also used when removing the user.  Value is 'yes' or 'no', default is 'no'.

*remove*:

* When used with a state of 'absent', the behavior denoted in the 'userdel' manpage for ``--remove`` is also used when removing the user.  Value is 'yes' or 'no', default is 'no'.

Example action from Ansible :doc:`playbooks`::

    user name=mdehaan comment=awesome passwd=awWxVV.JvmdHw createhome=yes
    user name=mdehaan groups=wheel,skynet
    user name=mdehaan state=absent force=yes

.. _virt:

virt
````

Manages virtual machines supported by libvirt.  Requires that libvirt be installed
on the managed machine.

*guest*:

* The name of the guest VM being managed

*state*

* Desired state of the VM.  Either `running`, `shutdown`, `destroyed`, or `undefined`.  Note that there may be some lag for state requests like 'shutdown', and these states only refer to the virtual machine states.  After starting a guest, the guest OS may not be immediately accessible.

*command*:

* In addition to state management, various non-idempotent commands are available for API and script usage (but don't make much sense in a playbook).  These mostly return information, though some also affect state.  See examples below.

Example action from Ansible :doc:`playbooks`::

    virt guest=alpha state=running
    virt guest=alpha state=shutdown
    virt guest=alpha state=destroyed
    virt guest=alpha state=undefined

Example guest management commands from /usr/bin/ansible::

    ansible host -m virt -a "guest=foo command=status"
    ansible host -m virt -a "guest=foo command=pause"
    ansible host -m virt -a "guest=foo command=unpause"
    ansible host -m virt -a "guest=foo command=get_xml"
    ansible host -m virt -a "guest=foo command=autostart"

Example host (hypervisor) management commands from /usr/bin/ansible::

    ansible host -m virt -a "command=freemem"
    ansible host -m virt -a "command=list_vms"
    ansible host -m virt -a "command=info"
    ansible host -m virt -a "command=nodeinfo"
    ansible host -m virt -a "command=virttype"

.. _yum:

yum
```

Will install, upgrade, remove, and list packages with the yum package manager.

*pkg*:

* A package name or package specifier with version, like name-1.0

*state*:

* Can be either 'installed', 'latest', or 'removed'.  The default is 'installed'. (In 0.4 and later, the aliases 'absent' and 'present' can also be used.  They correspond with 'removed' and 'installed')

*list*:

* When 'list' is supplied instead of 'state', the yum module can list
  various configuration attributes.  Values include 'installed', 'updates',
  'available', 'repos', or any package specifier.  (This is more intended for
  use with /usr/bin/ansible or the API, not playbooks.)

Example action from Ansible :doc:`playbooks`::

    yum pkg=httpd state=latest
    yum pkg=httpd state=removed
    yum pkg=httpd state=installed


Writing your own modules
````````````````````````

See :doc:`moduledev`.

.. seealso::

   :doc:`examples`
       Examples of using modules in /usr/bin/ansible
   :doc:`playbooks`
       Examples of using modules with /usr/bin/ansible-playbook
   :doc:`moduledev`
       How to write your own modules
   :doc:`api`
       Examples of using modules with the Python API
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

