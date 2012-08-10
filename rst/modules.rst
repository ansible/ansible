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
arguments, space delimited.  Some modules take no arguments, and the
command/shell modules simply take the string of the command you want to run.

From playbooks, Ansible modules are executed in a very similar way::

    - name: reboot the servers
      action: command /sbin/reboot -t now

All modules technically return JSON format data, though if you are using the
command line or playbooks, you don't really need to know much about
that.  If you're writing your own module, you care, and this means you do
not have to write modules in any particular language -- you get to choose.

Modules are `idempotent`, meaning they will seek to avoid changes to the system unless a change needs to be made.  When using Ansible
playbooks, these modules can trigger 'change events' in the form of notifying 'handlers'
to run additional tasks.

Let's see what's available in the Ansible module library, out of the box:

.. _apt:

apt
```

Manages apt-packages (such as for Debian/Ubuntu).

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | no       |         | A package name or package specifier with version, like `foo` or `foo=1.0`  |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              | no       | present | 'absent', 'present', or 'latest'.                                          |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| update_cache       | no       | no      | Run the equivalent of apt-get update before the operation.                 |
|                    |          |         | Can be run as part of the package installation or a seperate step          |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| purge              | no       | no      | Will forge purge of configuration files if state is set to 'absent'.       |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| default_release    | no       |         | Corresponds to the -t option for apt and sets pin priorities               |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| install_recommends | no       | yes     | Corresponds to the --no-install-recommends option for apt, default         |
|                    |          |         | behavior works as apt's default behavior, 'no' does not install            |
|                    |          |         | recommended packages.  Suggested packages are never installed.             |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| force              | no       | no      | If 'yes', force installs/removes.                                          |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    apt pkg=foo update-cache=yes
    apt pkg=foo state=removed
    apt pkg=foo state=installed
    apt pkg=foo=1.00 state=installed
    apt pkg=nginx state=latest default-release=squeeze-backports update-cache=yes
    apt pkg=openjdk-6-jdk state=latest install-recommends=no


.. _apt_repository:

apt_repository
``````````````

.. versionadded:: 0.7

Manages apt repositores

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| repo               | yes      |         | The repository name/value                                                  |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              | no       | present | 'absent' or 'present'                                                      |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    apt_repository repo=ppa:nginx/stable
    apt_repository repo='deb http://archive.canonical.com/ubuntu hardy partner'

.. _assemble:

assemble
````````

.. versionadded:: 0.5

Assembles a configuration file from fragments.  Often a particular
program will take a single configuration file and does not support a
conf.d style structure where it is easy to build up the configuration
from multiple sources.  Assmeble will take a directory of files that
have already been transferred to the system, and concatenate them
together to produce a destination file.  Files are assembled in string
sorting order.  Puppet calls this idea "fragments".

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| src                | yes      |         | An already existing directory full of source files                         |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dest               | yes      |         | A file to create using the concatenation of all of the source files        |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| OTHERS             |          |         | All arguments that the file module takes may also be used                  |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    assemble src=/etc/someapp/fragments dest=/etc/someapp/someapp.conf


.. _authorized_key:

authorized_key
``````````````

.. versionadded:: 0.5

Adds or removes an authorized key for a user from a remote host.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| user               | yes      |         | Name of the user who should have access to the remote host                 |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| key                | yes      |         | the SSH public key, as a string                                            |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              | no       | present | whether the given key should or should not be in the file                  |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    authorized_key user=charlie key="ssh-dss ASDF1234L+8BTwaRYr/rycsBF1D8e5pTxEsXHQs4iq+mZdyWqlW++L6pMiam1A8yweP+rKtgjK2httVS6GigVsuWWfOd7/sdWippefq74nppVUELHPKkaIOjJNN1zUHFoL/YMwAAAEBALnAsQN10TNGsRDe5arBsW8cTOjqLyYBcIqgPYTZW8zENErFxt7ij3fW3Jh/sCpnmy8rkS7FyK8ULX0PEy/2yDx8/5rXgMIICbRH/XaBy9Ud5bRBFVkEDu/r+rXP33wFPHjWjwvHAtfci1NRBAudQI/98DbcGQw5HmE89CjgZRo5ktkC5yu/8agEPocVjdHyZr7PaHfxZGUDGKtGRL2QzRYukCmWo1cZbMBHcI5FzImvTHS9/8B3SATjXMPgbfBuEeBwuBK5EjL+CtHY5bWs9kmYjmeo0KfUMH8hY4MAXDoKhQ7DhBPIrcjS5jPtoGxIREZjba67r6/P2XKXaCZH6Fc= charlie@example.org 2011-01-17"

.. _command:


command
```````

The command module takes the command name followed by a list of
arguments, space delimited.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| (free form)        | N/A      | N/A     | the command module takes a free form command to run                        |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| creates            | no       |         | a filename, when it already exists, this step will NOT be run              |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| chdir              | no       |         | cd into this directory before running the command (0.6 and later)          |
+--------------------+----------+---------+----------------------------------------------------------------------------+

The given command will be executed on all selected nodes.  It will not
be processed through the shell, so variables like "$HOME" and
operations like "<", ">", "|", and "&" will not work.  As such, all
paths to commands must be fully qualified.

.. note::
   If you want to run a command through the shell (say you are using
   '<', '>', '|', etc), you actually want the 'shell' module instead.
   The 'command' module is much more secure as it's not affected by
   the user's environment.

Example action from Ansible :doc:`playbooks`::

    command /sbin/shutdown -t now

creates and chdir can be specified after the command.  For instance, if you only want to run a command if a certain file does not exist, you can do the following::

    command /usr/bin/make_database.sh arg1 arg2 creates=/path/to/database

The `creates=` and `chdir` options will not be passed to the actual executable.


.. _copy:

copy
````

The copy module moves a file on the local box to remote locations.  In addition to the options
listed below, the arguments available to the `file` module can also be passed to the copy
module.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| src                | yes      |         | Local path to a file to copy to the remote server, can be absolute or      |
|                    |          |         | relative.                                                                  |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dest               | yes      |         | Remote absolute path where the file should end up                          |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| OTHERS             |          |         | All arguments the file module takes are also supported                     |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    copy src=/srv/myfiles/foo.conf dest=/etc/foo.conf owner=foo group=foo mode=0644



.. _easyinstall:

easy_install
````````````

.. versionadded:: 0.7

The easy_install module installs Python libraries.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | yes      |         | a Python library name                                                      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| virtualenv         | no       |         | an optional virtualenv directory path to install into, if the virtualenv   |
|                    |          |         | does not exist it is created automatically                                 |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    easy_install name=flask
    easy_install name=flask==0.8
    easy_install name=flask virtualenv=/srv/webapps/my_app/venv


.. _facter:

facter
``````

Runs the discovery program 'facter' on the remote system, returning
JSON data that can be useful for inventory purposes.

Requires that 'facter' and 'ruby-json' be installed on the remote end.

Playbooks do not actually use this module, they use the :ref:`setup`
module behind the scenes.

Example from /usr/bin/ansible::

    ansible foo.example.org -m ohai

.. _fetch:

fetch
`````

This module works like 'copy', but in reverse.  It is used for fetching files
from remote machines and storing them locally in a file tree, organized by hostname.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| src                | yes      |         | The file on the remote system to fetch.  This needs to be a file, not      |
|                    |          |         | a directory.  Recursive fetching may be supported in a later release.      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dest               | yes      |         | A directory to save the file into.  For example, if the 'dest' directory   |
|                    |          |         | is '/foo', a src file named '/tmp/bar' on host 'host.example.com', would   |
|                    |          |         | be saved into '/foo/host.example.com/tmp/bar'                              |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example::

    fetch src=/var/log/messages dest=/home/logtree

.. _file:

file
````

Sets attributes of files, symlinks, and directories, or removes files/symlinks/directories.  Many other modules
support the same options as the file module -- including 'copy', 'template', and 'assmeble'.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| dest               | yes      |         | defines the file being managed, unless when used with state=link, and      |
|                    |          |         | then sets the destination to create a symbolic link to using 'src'         |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              |          | file    | values are 'file', 'link', 'directory', or 'absent'.  If directory,        |
|                    |          |         | all immediate subdirectories will be created if they do not exist.  If     |
|                    |          |         | 'file', the file will NOT be created if it does not exist, see the 'copy'  |
|                    |          |         | or 'template' module if you want that behavior.  If 'link', the symbolic   |
|                    |          |         | link will be created or changed.  If absent, directories will be           |
|                    |          |         | recursively deleted, and files or symlinks will be unlinked.               |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| mode               |          |         | mode the file or directory shoudl be, such as 0644 as would be fed to      |
|                    |          |         | chmod.  English modes like 'g+x' are not yet supported                     |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| owner              |          |         | name of the user that should own the file/directory, as would be fed to    |
|                    |          |         | chown                                                                      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| group              |          |         | name of the group that should own the file/directory, as would be fed to   |
|                    |          |         | group                                                                      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| src                |          |         | path of the file to link to (applies only to state=link)                   |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| seuser             |          |         | user part of SELinux file context.  Will default to system policy, if      |
|                    |          |         | applicable.  If set to '_default', it will use the 'user' portion of the   |
|                    |          |         | the policy if available                                                    |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| serole             |          |         | role part of SELinux file context, '_default' feature works as above.      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| setype             |          |         | type part of SELinux file context, '_default' feature works as above       |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| selevel            |          | s0      | level part of the SELinux file context.  This is the MLS/MCS attribute,    |
|                    |          |         | sometimes known as the 'range'.  '_default' feature works as above         |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| context            |          |         | accepts only 'default' as a value.  This will restore a file's selinux     |
|                    |          |         | context in the policy.  Does nothing if no default is available.           |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    file path=/etc/foo.conf owner=foo group=foo mode=0644
    file path=/some/path owner=foo group=foo state=directory
    file path=/path/to/delete state=absent
    file src=/file/to/link/to dest=/path/to/symlink owner=foo group=foo state=link
    file path=/some/path state=directory setype=httpd_sys_content_t
    file path=/some/path state=directory context=default

.. _get_url:

get_url
```````

Downloads files from http, https, or ftp to the remote server.  The remote server must have direct
access to the remote resource.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| url                | yes      |         | http, https, or ftp URL                                                    |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dest               | yes      |         | absolute path of where to download the file to.  If dest is a directory,   |
|                    |          |         | the basename of the file on the remote server will be used.                |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| OTHERS             | no       |         | all arguments accepted by the file module also work here                   |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    - name: Grab a bunch of jQuery stuff
       action: get_url url=http://code.jquery.com/$item  dest=${jquery_directory} mode=0444
       with_items:
       - jquery.min.js
       - mobile/latest/jquery.mobile.min.js
       - ui/jquery-ui-git.css

.. _git:

git
```

Deploys software (or files) from git checkouts.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| repo               | yes      |         | git, ssh, or http protocol address of the git repo                         |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dest               | yes      |         | absolute path of where the repo should be checked out to                   |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| version            | no       | HEAD    | what version to check out -- either the git SHA, the literal string        |
|                    |          |         | 'HEAD', branch name, or a tag name.                                        |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| remote             | no       | origin  | name of the remote branch                                                  |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    git repo=git://foosball.example.org/path/to/repo.git dest=/srv/checkout version=release-0.22

.. _group:

group
`````

Adds or removes groups.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | yes      |         | name of the group                                                          |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| gid                |          |         | optional git to set for the group                                          |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              |          | present | 'absent' or 'present'                                                      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| system             |          | no      | if 'yes', indicates that the group being created is a system group.        |
+--------------------+----------+---------+----------------------------------------------------------------------------+

To control members of the group, see the users resource.

Example action from Ansible :doc:`playbooks`::

   group name=somegroup state=present

.. _mount:

mount
`````

The mount module controls active and configured mount points (fstab).

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | yes      |         | path to the mountpoint, ex: /mnt/foo                                       |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| src                | yes      |         | device to be mounted                                                       |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| fstype             | yes      |         | fstype                                                                     |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| opts               | no       |         | mount options (see fstab docs)                                             |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dump               | no       |         | dump (see fstab docs)                                                      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| passno             | no       |         | passno (see fstab docs)                                                    |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              | yes      |         | 'present', 'absent', 'mounted', or 'unmounted'.  If mounted/unmounted,     |
|                    |          |         | the device will be actively mounted or unmounted as well as just           |
|                    |          |         | configured in fstab.  'absent', and 'present' only deal with fstab.        |
+--------------------+----------+---------+----------------------------------------------------------------------------+

.. _mysql_db:

mysql_db
````````

Add or remove MySQL databases from a remote host.

Requires the MySQLdb Python package on the remote host. For Ubuntu, this is as easy as
apt-get install python-mysqldb.

+--------------------+----------+-----------+-----------------------------------------------------------------------------+
| parameter          | required | default   | comments                                                                    |
+====================+==========+===========+=============================================================================+
| name               | yes      |           | name of the database to add or remove                                       |
+--------------------+----------+-----------+-----------------------------------------------------------------------------+
| login_user         | no       |           | user name used to authenticate with                                         |
+--------------------+----------+-----------+-----------------------------------------------------------------------------+
| login_password     | no       |           | password used to authenticate with                                          |
+--------------------+----------+-----------+-----------------------------------------------------------------------------+
| login_host         | no       | localhost | host running the database                                                   |
+--------------------+----------+-----------+-----------------------------------------------------------------------------+
| state              | no       | present   | 'absent' or 'present'                                                       |
+--------------------+----------+-----------+-----------------------------------------------------------------------------+
| collation          | no       |           | collation mode                                                              |
+--------------------+----------+-----------+-----------------------------------------------------------------------------+
| encoding           | no       |           | encoding mode                                                               |
+--------------------+----------+-----------+-----------------------------------------------------------------------------+

Both 'login_password' and 'login_username' are required when you are passing credentials.
If none are present, the module will attempt to read the credentials from ~/.my.cnf, and
finally fall back to using the MySQL default login of 'root' with no password.

Example action from Ansible :doc:`playbooks`::

   - name: Create database
     action: mysql_db db=bobdata state=present


mysql_user
``````````

Adds or removes a user from a MySQL database.

Requires the MySQLdb Python package on the remote host. For Ubuntu, this is as easy as
apt-get install python-mysqldb.

+--------------------+----------+------------+----------------------------------------------------------------------------+
| parameter          | required | default    | comments                                                                   |
+====================+==========+============+============================================================================+
| name               | yes      |            | name of the user (role) to add or remove                                   |
+--------------------+----------+------------+----------------------------------------------------------------------------+
| password           | no       |            | set the user's password                                                    |
+--------------------+----------+------------+----------------------------------------------------------------------------+
| host               | no       | localhost  | the 'host' part of the MySQL username                                      |
+--------------------+----------+------------+----------------------------------------------------------------------------+
| login_user         | no       |            | user name used to authenticate with                                        |
+--------------------+----------+------------+----------------------------------------------------------------------------+
| login_password     | no       |            | password used to authenticate with                                         |
+--------------------+----------+------------+----------------------------------------------------------------------------+
| login_host         | no       | localhost  | host running MySQL.                                                        |
+--------------------+----------+------------+----------------------------------------------------------------------------+
| priv               | no       |            | MySQL privileges string in the format: db.table:priv1,priv2                |
+--------------------+----------+------------+----------------------------------------------------------------------------+
| state              | no       | present    | 'absent' or 'present'                                                      |
+--------------------+----------+------------+----------------------------------------------------------------------------+

Both 'login_password' and 'login_username' are required when you are passing credentials.
If none are present, the module will attempt to read the credentials from ~/.my.cnf, and
finally fall back to using the MySQL default login of 'root' with no password.

Example privileges string format:

    mydb.*:INSERT,UPDATE/anotherdb.*:SELECT/yetanotherdb.*:ALL

Example action from Ansible :doc:`playbooks`::

    - name: Create database user
      action: mysql_user name=bob passwd=12345 priv=*.*:ALL state=present

    - name: Ensure no user named 'sally' exists, also passing in the auth credentials.
      action: mysql_user login_user=root login_password=123456 name=sally state=absent


.. _ohai:

ohai
````

Similar to the :ref:`facter` module, this returns JSON inventory data.
Ohai data is a bit more verbose and nested than facter.

Requires that 'ohai' be installed on the remote end.

Playbooks should not call the ohai module, playbooks call the
:ref:`setup` module behind the scenes instead.

Example::

    ansible foo.example.org -m ohai

.. _ping:

ping
````

A trivial test module, this module always returns 'pong' on
successful contact.  It does not make sense in playbooks, but is useful
from /usr/bin/ansible::

    ansible webservers -m ping

.. postgresql_db:


.. _pip:

pip
```

.. versionadded:: 0.7

Manages Python library dependencies.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | no       |         | The name of a Python library to install                                    |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| version            | no       |         | The version number to install of the Python library specified in the       |
|                    |          |         | 'name' parameter                                                           |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| requirements       | no       |         | The path to a pip requirements file                                        |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| virtualenv         | no       |         | An optional path to a virtualenv directory to install into                 |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              | no       | present | 'present', 'absent' or 'latest'                                            |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Examples::

    pip name=flask
    pip name=flask version=0.8
    pip name=flask virtualenv=/srv/webapps/my_app/venv
    pip requirements=/srv/webapps/my_app/src/requirements.txt
    pip requirements=/srv/webapps/my_app/src/requirements.txt virtualenv=/srv/webapps/my_app/venv
    

postgresql_db
`````````````

Add or remove PostgreSQL databases from a remote host.

The default authentication assumes that you are either logging in as or
sudo'ing to the postgres account on the host.

This module uses psycopg2, a Python PostgreSQL database adapter. You must
ensure that psycopg2 is installed on the host before using this module. If
the remote host is the PostgreSQL server (which is the default case), then
PostgreSQL must also be installed on the remote host. For Ubuntu-based systems,
install the postgresql, libpq-dev, and python-psycopg2 packages on the remote
host before using this module.


+--------------------+----------+----------+----------------------------------------------------------------------------+
| parameter          | required | default  | comments                                                                   |
+====================+==========+==========+============================================================================+
| name               | yes      |          | name of the database to add or remove                                      |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| login_user         | no       | postgres | user (role) used to authenticate with PostgreSQL                           |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| login_password     | no       |          | password used to authenticate with PostgreSQL                              |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| login_host         | no       |          | host running PostgreSQL. Default (blank) implies localhost                 |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| state              |          | present  | 'absent' or 'present'                                                      |
+--------------------+----------+----------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    postgresql_db db=acme


.. postgresql_user:

postgresql_user
```````````````

Add or remove PostgreSQL users (roles) from a remote host, and grant the users
access to an existing database.

The default authentication assumes that you are either logging in as or
sudo'ing to the postgres account on the host.

This module uses psycopg2, a Python PostgreSQL database adapter. You must
ensure that psycopg2 is installed on the host before using this module. If
the remote host is the PostgreSQL server (which is the default case), then
PostgreSQL must also be installed on the remote host. For Ubuntu-based systems,
install the postgresql, libpq-dev, and python-psycopg2 packages on the remote
host before using this module.

+--------------------+----------+----------+----------------------------------------------------------------------------+
| parameter          | required | default  | comments                                                                   |
+====================+==========+==========+============================================================================+
| name               | yes      |          | name of the user (role) to add or remove                                   |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| password           | yes      |          | set the user's password                                                    |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| db                 | yes      |          | name of an existing database to grant user access to                       |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| login_user         | no       | postgres | user (role) used to authenticate with PostgreSQL                           |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| login_password     | no       |          | password used to authenticate with PostgreSQL                              |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| login_host         | no       |          | host running PostgreSQL. Default (blank) implies localhost                 |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| state              |          | present  | 'absent' or 'present'                                                      |
+--------------------+----------+----------+----------------------------------------------------------------------------+


Example action from Ansible :doc:`playbooks`::

    postgresql_user db=acme user=django password=ceec4eif7ya

.. _raw:

raw
```

Executes a low-down and dirty SSH command, not going through the module subsystem.

This is useful and should only be done in two cases.  The first case is installing
python-simplejson on older (python 2.4 and before) hosts that need it as a dependency
to run modules, since nearly all core modules require it.  Another is speaking to any
devices such as routers that do not have any Python installed.  In any other case,
using the 'shell' or 'command' module is much more appropriate.

Arguments given to 'raw' are run directly through the configured remote shell and
only output is returned.  There is no error detection or change handler support
for this module.

Example from `/usr/bin/ansible` to bootstrap a legacy python 2.4 host::

    ansible newhost.example.com raw -a "yum install python-simplejson"

.. _service:

service
```````

Controls services on remote machines.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | yes      |         | name of the service                                                        |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              | no       | started | 'started', 'stopped', 'reloaded', or 'restarted'.  Started/stopped are     |
|                    |          |         | idempotent actions that will not run commands unless neccessary.           |
|                    |          |         | 'restarted' will always bounce the service, 'reloaded' will always reload. |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| enabled            | no       |         | Whether the service should start on boot.  Either 'yes' or 'no'.           |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    service name=httpd state=started
    service name=httpd state=stopped
    service name=httpd state=restarted
    service name=httpd state=reloaded

.. _setup:

setup
`````

This module is automatically called by playbooks to gather useful variables about remote hosts that can be used
in playbooks.  It can also be executed directly by /usr/bin/ansible to check what variables are available
to a host.

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

Example action from `/usr/bin/ansible`::

    ansible testserver -m setup


.. _shell:

shell
`````

The shell module takes the command name followed by a list of
arguments, space delimited.  It is almost exactly like the command module
but runs the command through the user's configured shell on the remote node.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| (free form)        | N/A      | N/A     | the command module takes a free form command to run                        |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| creates            | no       |         | a filename, when it already exists, this step will NOT be run              |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| chdir              | no       |         | cd into this directory before running the command (0.6 and later)          |
+--------------------+----------+---------+----------------------------------------------------------------------------+

The given command will be executed on all selected nodes.

.. note::
   If you want to execute a command securely and predicably, it may be
   better to use the 'command' module instead.  Best practices when
   writing playbooks will follow the trend of using 'command' unless
   'shell' is explicitly required.  When running ad-hoc commands, use
   your best judgement.

Example action from a playbook::

    shell somescript.sh >> somelog.txt


.. _supervisorctl:

supervisorctl
`````````````

.. versionadded:: 0.7

Manage the state of a program or group of programs running via Supervisord

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | yes      |         | The name of the supervisord program/process to manage                      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              | yes      |         | 'started', 'stopped' or 'restarted'                                        |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from a playbook::

    supervisorctl name=my_app state=started


.. _template:

template
````````

Templates a file out to a remote server.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| src                | yes      |         | Path of a Jinja2 formatted template on the local server.  This can be      |
|                    |          |         | a relative or absolute path.                                               |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dest               | yes      |         | Location to render the template on the remote server                       |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| OTHERS             |          |         | This module also supports all of the arguments to the file module          |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from a playbook::

    template src=/srv/mytemplates/foo.j2 dest=/etc/foo.conf owner=foo group=foo mode=0644


.. _user:

user
````

Creates user accounts, manipulates existing user accounts, and removes user accounts.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | yes      |         | name of the user to create, remove, or edit                                |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| comment            |          |         | optionally sets the description of the user                                |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| uid                |          |         | optionally sets the uid of the user                                        |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| group              |          |         | optionally sets the user's primary group (takes a group name)              |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| groups             |          |         | puts the user in this comma-delimited list of groups                       |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| append             |          | no      | if 'yes', will only add groups, not set them to just the list in 'groups'  |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| shell              |          |         | optionally set the user's shell                                            |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| createhome         |          | yes     | unless 'no', a home directory will be made for the user                    |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| home               |          |         | sets where the user's homedir should be, if not the default                |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| password           |          |         | optionally set the user's password to this crypted value.  See the user's  |
|                    |          |         | example in the github examples directory for what this looks like in a     |
|                    |          |         | playbook                                                                   |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              |          | present | when 'absent', removes the user.                                           |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| system             |          | no      | only when initially creating, setting this to 'yes' makes the user a       |
|                    |          |         | system account.  This setting cannot be changed on existing users.         |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| force              |          | no      | when used with state=absent, behavior is as with userdel --force           |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| remove             |          | no      | when used with state=remove, behavior is as with userdel --remove          |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    user name=mdehaan comment=awesome passwd=awWxVV.JvmdHw createhome=yes
    user name=mdehaan groups=wheel,skynet
    user name=mdehaan state=absent force=yes

.. _virt:

virt
````

Manages virtual machines supported by libvirt.  Requires that libvirt be installed
on the managed machine.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | yes      |         | name of the guest VM being managed                                         |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              |          |         | 'running', 'shutdown', 'destroyed', or 'undefined'.  Note that there may   |
|                    |          |         | be some lag for state requests like 'shutdown' since these refer only to   |
|                    |          |         | VM states.  After starting a guest, it may not be immediately accessible.  |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| command            |          |         | in addition to state management, various non-idempotent commands are       |
|                    |          |         | available.  See examples below.                                            |
+--------------------+----------+---------+----------------------------------------------------------------------------+

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

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | yes      |         | package name, or package specifier with version, like 'name-1.0'           |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              |          | present | 'present', 'latest', or 'absent'.                                          |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| list               |          |         | various non-idempotent commands for usage with /usr/bin/ansible and not    |
|                    |          |         | playbooks.  See examples below.                                            |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    yum name=httpd state=latest
    yum name=httpd state=removed
    yum name=httpd state=installed


Additional Contrib Modules
``````````````````````````

In addition to the following built-in modules, community modules are available at `Ansible Resources <http://github.com/ansible/ansible-resources>`_.


Writing your own modules
````````````````````````

See :doc:`moduledev`.

.. seealso::

   `Ansible Resources (Contrib) <https://github.com/ansible/ansible-resources>`_
       User contributed playbooks, modules, and articles
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

