Ansible Modules
===============

Ansible ships with a number of modules that can be executed directly
on remote hosts or through ansible playbooks.

.. seealso::

   :doc:`examples`
       Examples of using modules in /usr/bin/ansible
   :doc:`playbooks`
       Examples of using modules with /usr/bin/ansible-playbook
   :doc:`api`
       Examples of using modules with the Python API

Nearly all modules take ``key=value`` parameters, space delimited.  Some modules take
no parameters, and the command/shell modules simply take the string
of the command you want to run.

All modules return JSON format data, though if you are using the
command line or playbooks, you don't really need to know much about
that.

Most modules other than command are idempotent, meaning they will seek
to avoid changes unless a change needs to be made.  When using ansible
playbooks, these modules can trigger change events.  Unless otherwise
noted, all modules support change hooks.

Stock modules:

.. _command:

command
```````

The command module takes the command name followed by a list of
arguments, space delimited.  

If you want to run a command through the shell (say you are using
'<', '>', '|', etc), you actually want the 'shell' module instead.  
The 'command' module is much more secure as it's not affected by the user's environment.

Example usage::

    /sbin/shutdown -t now

The given command will be executed on all selected nodes.  It will not
be processed through the shell, so variables like "$HOME" and 
operations like "<", ">", "|", and "&" will not work.  As such, all
paths to commands must be fully qualified.

This module does not support change hooks and returns the return code
from the program as well as timing information about how long the
command was running for.


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


.. _shell:

shell
`````

The shell module takes the command name followed by a list of
arguments, space delimited.  It is almost exactly like the command module
but runs the command through the shell rather than directly.

Example usage::

    find . | grep *.txt

The given command will be executed on all selected nodes.  

If you want to execute a command securely and predicably, it may
be better to use the 'command' module instead.  Best practices
when writing playbooks will follow the trend of using 'command'
unless 'shell' is explicitly required.  When running ad-hoc commands,
use your best judgement.

This module does not support change hooks and returns the return code
from the program as well as timing information about how long the
command was running for.


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

Writing your own modules
````````````````````````

To write your own modules, simply follow the convention of those
already available in /usr/share/ansible.  Modules must return JSON but
can be written in any language.  Modules should return hashes, but
hashes can be nested.

To support change hooks, modules should return hashes with a changed:
True/False element at the top level::

    {
        'changed'   : True,
        'something' : 42
    }

Modules can also choose to indicate a failure scenario by returning a
top level ``failure`` element with a True value, and a ``msg`` element
describing the nature of the failure.  Other return values are up to
the module::

    {
        'failure'   : True,
        'msg'       : "here is what happened..."
    }

When shipping modules, drop them in /usr/share/ansible, or specify the
module path to the command line tool or API.  It is easy to test
modules by running them directly on the command line, passing them
arguments just like they would be passed with ansible.
