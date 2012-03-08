Ansible Modules
===============

.. seealso::

   :doc:`examples`
       Examples of using modules in /usr/bin/ansible
   :doc:`playbooks`
       Examples of using modules with /usr/bin/ansible-playbook
   :doc:`api`
       Examples of using modules with the Python API


About Modules
`````````````

Ansible ships with a number of modules that can be executed directly on remote hosts or through
ansible playbooks.


Idempotence
```````````

Most modules other than command are idempotent, meaning they will seek to avoid changes
unless a change needs to be made.  When using ansible playbooks, these modules can
trigger change events.  Unless otherwise noted, all modules support change hooks.


command
```````

The command module takes the command name followed by a list of arguments, space delimited.
This is the only module that does not use key=value style parameters.

Example usage::

    /sbin/shutdown -t now

This module does not support change hooks and returns the return code from the program as well as timing information about how long the command was running for.


copy
````

The copy module moves a file on the local box to remote locations.  

*src*::

Local absolute path to a file to copy to the remote server


*dest*::

Remote absolute path where the file should end up


This module also returns md5sum information about the resultant file.


facter
``````

Runs the discovery program 'facter' on the remote system, returning
JSON data that can be useful for inventory purposes.

Requires that 'facter' and 'ruby-json' be installed on the remote end.

This module is informative only - it takes no parameters & does not support change hooks,
nor does it make any changes on the system.


git
```

Deploys software from git checkouts.

*repo*::

git or http protocol address of the repo to checkout

*dest*::

where to check it out, an absolute directory path

*version*::

what version to check out -- either the git SHA, the literal string 'HEAD', or a tag name


ohai
````

Similar to the facter module, this returns JSON inventory data.  Ohai
data is a bit more verbose and nested than facter.

Requires that 'ohai' be installed on the remote end.

This module is information only - it takes no parameters & does not
support change hooks, nor does it make any changes on the system.


ping
````

A trivial test module, this module always returns the integer '1' on
successful contact.

This module does not support change hooks.

This module is informative only - it takes no parameters & does not
support change hooks, nor does it make any changes on the system.


service
```````

Controls services on remote machines.

*state*

Values are 'started', 'stopped', or 'restarted'.   Started/stopped
are idempotent actions that will not run commands unless neccessary.
'restarted' will always bounce the service


*name*

The name of the service


setup
`````

Writes a JSON file containing key/value data, for use in templating.
Call this once before using the template modules.  Playbooks will
execute this module automatically as the first step in each play.

If facter or ohai are installed, variables from these programs will also
be snapshotted into the JSON file for usage in templating. These variables
are prefixed with 'facter_' and 'ohai_" so it's easy to tell their source.

*metadata*

Optionally overrides the default JSON file location of /etc/ansible/setup or ~/ansible/setup
depending on what remote user has been specified.  

If used, also supply the metadata parameter to the template module.

*anything*

any other parameters can be named basically anything, and set a key=value
pair in the JSON file for use in templating.


template
````````

Templates a file out to a remote server.  Call the setup module prior to usage.

*src*

path of a Jinja2 formatted template on the local server


*dest*

location to render the template on the remote server


*metadata*

location of a JSON file to use to supply template data.  Default is /etc/ansible/setup
which is the same as the default for the setup module.   Change if running as a non-root
remote user who does not have permissions on /etc/ansible.


This module also returns md5sum information about the resultant file.


user
````

This module is in plan.


yum
```

This module is in plan.


WRITING YOUR OWN MODULES
````````````````````````

To write your own modules, simply follow the convention of those already available in
/usr/share/ansible.  Modules must return JSON but can be written in any language.
Modules should return hashes, but hashes can be nested.
To support change hooks, modules should return hashes with a changed: True/False
element at the top level.  Modules can also choose to indicate a failure scenario
by returning a top level 'failure' element with a True value, and a 'msg' element
describing the nature of the failure.  Other values are up to the module.
