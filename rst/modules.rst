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
not have to write modules in any particular language -- you get tho choose.

Most modules other than command are `idempotent`, meaning they will seek
to avoid changes to the system unless a change needs to be made.  When using Ansible
playbooks, these modules can trigger 'change events'.  Unless otherwise
noted, any given module does support change hooks.

Let's see what's available in the Ansible module library, out of the box:

.. _command:

apt
```

Manages apt-packages (such as for Debian/Ubuntu).

*pkg*:

* A package name or package specifier with version, like name-1.0

*state*:

* Can be either 'installed' or 'removed'.   NOTE:  support
for 'latest' (see yum, below) is in work.

Example action from Ansible :doc:`playbooks`::

    apt pkg=foo ensure=removed
    apt pkg=foo ensure=installed


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
command was running for.

Example action from Ansible :doc:`playbooks`::

    command /sbin/shutdown -t now


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

file
````

Sets attributes of files and directories, or removes files/directories.  All parameters available 
to the file module are also available when running the `copy` or `template` modules.

*dest*:

* absolute path to a file on the filesystem.

*state*:

* either 'file', 'directory', or 'absent'.  The default is 'file'.  If 'directory', the directory and all immediate subdirectories will be created if they do not exist.  If 'file', the file will NOT be created if it does not exist, specify `copy` or `template` for the module name instead if you need to put content at the specified location.  If 'absent', directories will be recursively deleted, and files or symlinks will be unlinked.

*mode*:

* the mode the file or directory should be, such as 644, as would be given to `chmod`.  English modes like "g+x" are not yet supported.

*owner*:

* name of user that should own the file or directory, as would be given to `chown`.

*group*:

* name of group that should own the file or directory, as would be given to `chgrp`

Example action from Ansible :doc:`playbooks`::

    file dest=/etc/foo.conf owner=foo group=foo mode=0644
    file dest=/some/path owner=foo group=foo state=directory
    file dest/path/to/delete state=absent


git
```

Deploys software (or files) from git checkouts.

*repo*:

* git or http protocol address of the repo to checkout.

*dest*:

* Where to check it out, an absolute directory path.

*version*:

* What version to check out -- either the git SHA, the literal string
  ``HEAD``, or a tag name.

Example action from Ansible :doc:`playbooks`::

    git repo=git://foosball.example.org/path/to/repo.git dest=/srv/checkout version=release-0.22


ohai
````

Similar to the :ref:`facter` module, this returns JSON inventory data.
Ohai data is a bit more verbose and nested than facter.

Requires that 'ohai' be installed on the remote end.

This module is information only - it takes no parameters & does not
support change hooks, nor does it make any changes on the system.

Playbooks should not call the ohai module, playbooks call the
:ref:`setup` module behind the scenes instead.

ping
````

A trivial test module, this module always returns the integer ``1`` on
successful contact.

This module does not support change hooks and is informative only - it
takes no parameters & does not support change hooks, nor does it make
any changes on the system.


service
```````

Controls services on remote machines.

*state*:

* Values are ``started``, ``stopped``, or ``restarted``.
  Started/stopped are idempotent actions that will not run commands
  unless necessary.  ``restarted`` will always bounce the service.

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

If facter or ohai are installed, variables from these programs will
also be snapshotted into the JSON file for usage in templating. These
variables are prefixed with ``facter_`` and ``ohai_`` so it's easy to
tell their source.  All variables are then bubbled up to the caller.

*anything*:

 * Any other parameters can be named basically anything, and set a
   ``key=value`` pair in the JSON file for use in templating.

Example action from Ansible :doc:`playbooks`::

    vars:
        ntpserver: 'ntp.example.com'
        xyz: 1234

Example action from `/usr/bin/Ansible`::

    Ansible -m all setup -a "ntpserver=ntp.example.com xyz=1234"


.. _shell:

shell
`````

The shell module takes the command name followed by a list of
arguments, space delimited.  It is almost exactly like the command module
but runs the command through the shell rather than directly.

The given command will be executed on all selected nodes.  

If you want to execute a command securely and predicably, it may
be better to use the 'command' module instead.  Best practices
when writing playbooks will follow the trend of using 'command'
unless 'shell' is explicitly required.  When running ad-hoc commands,
use your best judgement.

This module does not support change hooks and returns the return code
from the program as well as timing information about how long the
command was running for.

Example action from a playbook::

    shell somescript.sh >> somelog.txt


.. _template:

template
````````

Templates a file out to a remote server.  Call the :ref:`setup` module
prior to usage if you are not running from a playbook.   In addition to the options
listed below, the arguments available to the `file` module can also be passed to the copy
module.   

*src*:

* Path of a Jinja2 formatted template on the local server.  This can
  be a relative or absolute path.

*dest*:

* Location to render the template on the remote server.

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

*gid*:

* Optionally sets the primary group GID.  The user module will also be able to manipulate this.

*shell*:

* Optionally sets the user's shell.

*createhome*:

* Whether to create the user's home directory.  Takes 'yes', or 'no'.  The default is 'yes'.
    
*password*:

* Sets the user's password to this crypted value.  Pass in a result from crypt.  See the users
  example in the github examples directory for what this looks like in a playbook.

*state*:

* Defaults to 'present'.  When 'absent', the user account will be removed if present.

Example action from Ansible :doc:`playbooks`::

    user name=mdehaan comment=awesome passwd=awWxVV.JvmdHw createhome=yes
    user name=mdehaan state=absent

.. _yum:

yum
```

Will install, upgrade, remove, and list packages with the yum package manager.

*pkg*:

* A package name or package specifier with version, like name-1.0

*state*:

* Can be either 'installed', 'latest', or 'removed'

*list*:

* When 'list' is supplied instead of 'state', the yum module can list
  various configuration attributes.  Values include 'installed', 'updates',
  'available', 'repos', or any package specifier.

Example action from Ansible :doc:`playbooks`::

    yum pkg=httpd ensure=latest
    yum pkg=httpd ensure=removed
    yum pkg=httpd ensure=installed


Writing your own modules
````````````````````````

See :doc:`moduledev`.

.. seealso::

   :doc:`examples`
       Examples of using modules in /usr/bin/Ansible
   :doc:`playbooks`
       Examples of using modules with /usr/bin/Ansible-playbook
   :doc:`moduledev`
       How to write your own modules
   :doc:`api`
       Examples of using modules with the Python API
   `Mailing List <http://groups.google.com/group/Ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

