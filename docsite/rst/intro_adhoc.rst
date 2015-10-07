Introduction To Ad Hoc Commands
===============================

.. contents:: Topics

.. highlight:: bash

.. index::
  pair: introduction; ad hoc commands

*What is an ad hoc command?*

An ad hoc command is something that you might type in to accomplish a quick task, but do not want to save for later.   

This is a good place to start to understand the basics of what Ansible can do prior to learning the playbooks language -- ad hoc commands can also be used to do quick things where writing a full playbook is unnecessary. Generally speaking, the true power of Ansible lies in playbooks.

*Why would you use ad hoc tasks versus playbooks?*

For example, if you wanted to power off all of your lab systems for Christmas vacation, you could execute a quick one-liner in Ansible without writing a playbook.

For configuration management and deployments, however, you will want to use ``/usr/bin/ansible-playbook`` and the concepts you are learning will 
port over directly to the playbook language. Refer :doc:`playbooks` for more information.

If you have not yet read :doc:`intro_inventory`, be sure to take the time to review it before proceeding.

The following examples show how to use ``/usr/bin/ansible`` for running ad hoc tasks. 

.. _parallelism_and_shell_commands:

Parallelism and Shell Commands
````````````````````````````````

.. index::
  pair: ad hoc commands; parallelism
  pair: ad hoc commands; shell commands

To better explain parallelism and shell commands in relation to ad hoc commands, use the following arbitrary example.

Say that you want use Ansible's command line tool to reboot all web servers in Atlanta, 10 at a time.  First, you should
set up an ``ssh-agent`` so it can remember your credentials:

::

    $ ssh-agent bash
    $ ssh-add ~/.ssh/id_rsa

If you would prefer to use SSH with a password instead of using ``ssh-agent`` with keys, you can do so with the ``--ask-pass`` (``-k``) flags, but this method is not recommended over using ssh-agent.

To run the reboot command on all servers in a group, in this case *atlanta*, in 10 parallel forks, use the following:

::

    $ ansible atlanta -a "/sbin/reboot" -f 10

The ``/usr/bin/ansible`` file defaults to running from your user account.  If you do not like this behavior, pass in ``-u username``.  If you want to run commands as a different user, use the following:

::

    $ ansible atlanta -a "/usr/bin/foo" -u username

Often, you may find yourself not wanting to do tasks from your user account.  To run commands through ``sudo``, use the following:

::

    $ ansible atlanta -a "/usr/bin/foo" -u username --sudo [--ask-sudo-pass]

Use ``--ask-sudo-pass`` (``-K``) if you are not using "passwordless" ``sudo``.  This interactively prompts you for the password to use.
Use of "passwordless" ``sudo`` makes things easier to automate, but it is not required.

It is also possible to sudo to a user other than root using ``--sudo-user`` (``-U``):

::

    $ ansible atlanta -a "/usr/bin/foo" -u username -U otheruser [--ask-sudo-pass]

.. note::
   
    While rare, some users have security rules where they need to constrain their sudo environment to running specific command paths only.  
    This does not work with Ansible's no-bootstrapping philosophy and hundreds of different modules. If this approach is necessary, you should use Ansible from a special account that does not have this constraint. One way to accomplish this, without sharing access to unauthorized users, would be gating Ansible with :doc:`tower`, which can hold on to an SSH credential and let members of certain organizations use it on their behalf without having direct access.

.. tip::

    You should now have a basic understanding of how ad hoc commands are used. If you have not read about patterns and groups yet, now is a good time to go back and review :doc:`intro_patterns`.


The ``-f 10`` in the above example (``$ ansible atlanta -a "/sbin/reboot" -f 10``) specifies the usage of 10 simultaneous processes to use.   You can also set this in :doc:`intro_configuration` to avoid setting it again.  The number of simultaneous processes to use is set at 5 by default, which is very conservative.  You will likely want to talk to a lot more simultaneous hosts, so feel free to set this number to a higher value.  If you have more hosts than the value set for the fork count, Ansible will still talk to them, but it will take a little longer.  Just remember that you can adjust this value to be as high as your system can handle.

.. index::
  pair: ad hoc; shell module
  pair: ad hoc; command module

You can also select which Ansible "module" you want to run.  Normally, commands use ``-m`` for module name, but the default module name is 'command' and it is not necessary to specify that all of the time.  You will notice the use of ``-m`` in later examples to run some other :doc:`modules`.

.. note::

   The :ref:`command` module does not support shell variables and things like piping.  To execute a module using a
   shell, use the ``shell`` module instead. Read more about the differences on the :doc:`modules` page. 


Using the :ref:`shell` module looks like the following:

::

    $ ansible raleigh -m shell -a 'echo $TERM'


When running any command with the Ansible ad hoc CLI (as opposed to :doc:`Playbooks <playbooks>`), pay particular attention to shell quoting rules, so the local shell doesn't eat a variable before it gets passed to Ansible. For example, using double rather than single quotes in the above example would evaluate the variable on the box you were on.

So far, you have learned about simple command execution, but most Ansible modules usually do not work like simple scripts. Instead, they make the remote system appear like you designate that it should, as well as run the commands necessary to get it there.  This is commonly referred to as *idempotence*, which is a core design goal of Ansible. However, the need to run arbitrary commands is recognized as equally important, so Ansible easily supports both.

.. _file_transfer:

.. index::
  pair: ad hoc; file transfer

File Transfer
`````````````

The following provides another example use case for the ``/usr/bin/ansible`` command line interface.  

Ansible can SCP lots of files to multiple machines in parallel. To transfer a file directly to many servers:

::

    $ ansible atlanta -m copy -a "src=/etc/hosts dest=/tmp/hosts"

If you use playbooks, you can also take advantage of the ``template`` module, which takes this another step further.  (Refer to the :ref:`about_modules` and :ref:`playbooks` documentation for more information.)

The ``file`` module allows changing ownership and permissions on files.  These same options can be passed directly to the ``copy`` module as well:

::

    $ ansible webservers -m file -a "dest=/srv/foo/a.txt mode=600"
    $ ansible webservers -m file -a "dest=/srv/foo/b.txt mode=600 owner=josiedog group=josiedog"

The ``file`` module can also create directories, similar to the ``mkdir -p`` command:

::

    $ ansible webservers -m file -a "dest=/path/to/c mode=755 owner=josiedog group=josiedog state=directory"

As well as delete directories (recursively) and delete files::

    $ ansible webservers -m file -a "dest=/path/to/c state=absent"

.. _managing_packages:

.. index::
  pair: ad hoc; managing packages
  pair: ad hoc; package management

Managing Packages
`````````````````

There are modules available for ``yum`` and ``apt``.  Here are some examples using ``yum`` commands.

To ensure a package is installed *without* updating it:

::

    $ ansible webservers -m yum -a "name=acme state=present"

To ensure a package is installed to a specific version:

::

    $ ansible webservers -m yum -a "name=acme-1.5 state=present"

To ensure a package is at the latest version:

::

    $ ansible webservers -m yum -a "name=acme state=latest"

To ensure a package is not installed:

::

    $ ansible webservers -m yum -a "name=acme state=absent"

Ansible has modules for managing packages under many platforms.  If your package manager does not have a module available for it, you can install
for other packages using the command module or (even better and highly encouraged) you can contribute a module for other package managers.  Check out the mailing list for details (refer to :ref:`community_contributing` for more information).

.. _users_and_groups:

.. index::
  pair: ad hoc; users
  pair: ad hoc; groups

Users and Groups
````````````````

The ``user`` module allows for the easy creation and manipulation of existing user accounts, as well as for the removal of user accounts that may
exist:

::

    $ ansible all -m user -a "name=foo password=<crypted password here>"

    $ ansible all -m user -a "name=foo state=absent"

Refer to the :doc:`modules` section for details on all of the available options, including how to manipulate groups and group membership.

.. _from_source_control:

.. index::
    pair: ad hoc; source control
    pair: ad hoc; deploying from source control
    pair: source control; deployment

Deploying From Source Control
`````````````````````````````

You can deploy your webapp straight from ``git``, using the following as an example:

::

    $ ansible webservers -m git -a "repo=git://foo.example.org/repo.git dest=/srv/myapp version=HEAD"

Since Ansible modules can notify change handlers it is possible to tell Ansible to run specific tasks when the code is updated, such as
deploying Perl/Python/PHP/Ruby directly from git and then restarting apache.

.. _managing_services:

.. index::
    pair: ad hoc; managing services

Managing Services
`````````````````

To ensure a service is started on all webservers:

::

    $ ansible webservers -m service -a "name=httpd state=started"

Alternatively, to restart a service on all webservers:

::

    $ ansible webservers -m service -a "name=httpd state=restarted"

To ensure a service is stopped:

::

    $ ansible webservers -m service -a "name=httpd state=stopped"

.. _time_limited_background_operations:

.. index::
    pair: ad hoc; background operations (time limited)
    paor: ad hoc; polling

Time Limited Background Operations
````````````````````````````````````

Long running operations can be backgrounded, and their status can be checked on
later. If you kick hosts and don't want to poll, it looks like this:

::

    $ ansible all -B 3600 -P 0 -a "/usr/bin/long_running_operation --do-stuff"

If you do decide you want to check on the job status later, you can use the
``async_status`` module, passing to it the job id that was returned when you ran
the original job in the background:

::

    $ ansible web1.example.com -m async_status -a "jid=488359678239.2844"

Polling is built-in and looks like this:

::

    $ ansible all -B 1800 -P 60 -a "/usr/bin/long_running_operation --do-stuff"

The above example says "run for 30 minutes max (``-B``: 30*60=1800), poll for status (``-P``) every 60 seconds".

Poll mode is smart and all jobs are started before polling begins on any machine. Be sure to use a high enough ``--forks`` value if you want to get all of your jobs started very quickly. After the time limit (in seconds) runs out (``-B``), the process on the remote nodes is terminated.

Typically, you will be backgrounding long-running shell commands or software upgrades only.  Backgrounding the ``copy`` module does not do a background file transfer.  :doc:`Playbooks <playbooks>` also support polling and have a simplified syntax for this.

.. _checking_facts:

.. index:: 
  pair: ad hoc; facts, gathering

Gathering Facts
````````````````

Facts are described in the playbooks section and represent discovered variables about a system.  These can be used to implement conditional execution of tasks but also just to get ad hoc information about your system. You can view all facts using the following command:

::

    $ ansible all -m setup

It is also possible to filter this output to just export certain facts. Refer to the ``setup`` module's documentation for details.

Read more about facts in the :doc:`playbooks_variables` section of :doc:`Playbooks <playbooks>`. 

.. seealso::

   :doc:`intro_configuration`
       All about the Ansible config file
   :doc:`modules`
       A list of available modules
   :doc:`playbooks`
       Using Ansible for configuration management & deployment
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
