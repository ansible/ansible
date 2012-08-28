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


======================= ======================= ======================= 
:ref:`apt_repository`   :ref:`apt`              :ref:`assemble`
:ref:`authorized_key`   :ref:`command`          :ref:`copy`
:ref:`easy_install`     :ref:`facter`           :ref:`fetch`
:ref:`file` 		:ref:`get_url` 		:ref:`git`
:ref:`group` 		:ref:`mount` 		:ref:`mysql_db`
:ref:`mysql_user` 	:ref:`nagios` 		:ref:`ohai`
:ref:`ping` 		:ref:`pip` 		:ref:`postgresql_db`
:ref:`postgresql_user` 	:ref:`raw` 		:ref:`service`
:ref:`setup` 		:ref:`shell` 		:ref:`supervisorctl`
:ref:`template` 	:ref:`user` 		:ref:`virt`
:ref:`yum`
======================= ======================= ======================= 

.. include:: modules/apt_repository.rst
.. include:: modules/apt.rst
.. include:: modules/assemble.rst
.. include:: modules/authorized_key.rst
.. include:: modules/command.rst
.. include:: modules/copy.rst
.. include:: modules/easy_install.rst
.. include:: modules/facter.rst
.. include:: modules/fetch.rst
.. include:: modules/file.rst
.. include:: modules/get_url.rst
.. include:: modules/git.rst
.. include:: modules/group.rst
.. include:: modules/mount.rst
.. include:: modules/mysql_db.rst
.. include:: modules/mysql_user.rst
.. include:: modules/nagios.rst
.. include:: modules/ohai.rst
.. include:: modules/ping.rst
.. include:: modules/pip.rst
.. include:: modules/postgresql_db.rst
.. include:: modules/postgresql_user.rst
.. include:: modules/raw.rst
.. include:: modules/service.rst
.. include:: modules/setup.rst
.. include:: modules/shell.rst
.. include:: modules/supervisorctl.rst
.. include:: modules/template.rst
.. include:: modules/user.rst
.. include:: modules/virt.rst
.. include:: modules/yum.rst



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

