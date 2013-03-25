.. _patterns:

Inventory & Patterns
====================

.. image:: http://ansible.cc/docs/_static/ansible_fest_2013.png
   :alt: ansiblefest 2013
   :target: http://ansibleworks.com/fest


Ansible works against multiple systems in your infrastructure at the
same time.  It does this by selecting portions of systems listed in
Ansible's inventory file, which defaults to /etc/ansible/hosts.

.. contents:: `Table of contents`
   :depth: 2
   :backlinks: top

.. _inventoryformat:

Hosts and Groups
++++++++++++++++

The format for /etc/ansible/hosts is an INI format and looks like this::

    mail.example.com

    [webservers]
    foo.example.com
    bar.example.com

    [dbservers]
    one.example.com
    two.example.com
    three.example.com

The things in brackets are group names. You don't have to have them,
but they are useful.

If you have hosts that run on non-standard SSH ports you can put the port number
after the hostname with a colon.  Ports listed in any SSH config file won't be read,
so it is important that you set them if things are not running on the default port::

    badwolf.example.com:5309

Suppose you have just static IPs and want to set up some aliases that don't live in your host file, or you are connecting through tunnels.  You can do things like this::

    jumper ansible_ssh_port=5555 ansible_ssh_host=192.168.1.50

In the above example, trying to ansible against the host alias "jumper" (which may not even be a real hostname) will contact 192.168.1.50 on port 5555.

Adding a lot of hosts?  In 0.6 and later, if you have a lot of hosts following similar patterns you can do this rather than listing each hostname::

    [webservers]
    www[01:50].example.com


In 1.0 and later, you can also do this for alphabetic ranges::

    [databases]
    db-[a:f].example.com

For numeric patterns, leading zeros can be included or removed, as desired. Ranges are inclusive.

In 1.1 and later, you can also select the connection type and user on a per host basis::

   [targets]

   localhost              ansible_connection=local
   other1.example.com     ansible_connection=ssh        ansible_ssh_user=mpdehaan
   other2.example.com     ansible_connection=ssh        ansible_ssh_user=mdehaan

All of these variables can of course also be set outside of the inventory file, in 'host_vars' if you wish
to keep your inventory file simple.

Selecting Targets
+++++++++++++++++

We'll go over how to use the command line in :doc:`examples` section, however, basically it looks like this::

    ansible <pattern_goes_here> -m <module_name> -a <arguments>

Such as::

    ansible webservers -m service -a "name=httpd state=restarted"

Within :doc:`playbooks`, these patterns can be used for even greater purposes.

Anyway, to use Ansible, you'll first need to know how to tell Ansible which hosts in your inventory file to talk to.
This is done by designating particular host names or groups of hosts.

The following patterns target all hosts in the inventory file::

    all
    *

Basically 'all' is an alias for '*'.  It is also possible to address a specific host or hosts::

    one.example.com
    one.example.com:two.example.com
    192.168.1.50
    192.168.1.*

The following patterns address one or more groups, which are denoted
with the aforementioned bracket headers in the inventory file::

    webservers
    webservers:dbservers

You can exclude groups as well, for instance, all webservers not in Phoenix::

    webservers:!phoenix

You can also specify the intersection of two groups::

    webservers:&staging

You can do combinations::

    webservers:dbservers:!phoenix:&staging

You can also use variables::

    webservers:!$excluded:&$required

Individual host names, IPs and groups, can also be referenced using
wildcards::

    *.example.com
    *.com

It's also ok to mix wildcard patterns and groups at the same time::

    one*.com:dbservers


Easy enough.  See :doc:`examples` and then :doc:`playbooks` for how to do things to selected hosts.

Host Variables
++++++++++++++

It is easy to assign variables to hosts that will be used later in playbooks::

   [atlanta]
   host1 http_port=80 maxRequestsPerChild=808
   host2 http_port=303 maxRequestsPerChild=909


Group Variables
+++++++++++++++

Variables can also be applied to an entire group at once::

   [atlanta]
   host1
   host2

   [atlanta:vars]
   ntp_server=ntp.atlanta.example.com
   proxy=proxy.atlanta.example.com

Groups of Groups, and Group Variables
+++++++++++++++++++++++++++++++++++++

It is also possible to make groups of groups and assign
variables to groups.  These variables can be used by /usr/bin/ansible-playbook, but not
/usr/bin/ansible::

   [atlanta]
   host1
   host2

   [raleigh]
   host2
   host3

   [southeast:children]
   atlanta
   raleigh

   [southeast:vars]
   some_server=foo.southeast.example.com
   halon_system_timeout=30
   self_destruct_countdown=60
   escape_pods=2

   [usa:children]
   southeast
   northeast
   southwest
   southeast

If you need to store lists or hash data, or prefer to keep host and group specific variables
separate from the inventory file, see the next section.

Splitting Out Host and Group Specific Data
++++++++++++++++++++++++++++++++++++++++++

.. versionadded:: 0.6

In addition to the storing variables directly in the INI file, host
and group variables can be stored in individual files relative to the
inventory file.  These variable files are in YAML format.

Assuming the inventory file path is::

    /etc/ansible/hosts

If the host is named 'foosball', and in groups 'raleigh' and 'webservers', variables
in YAML files at the following locations will be made available to the host::

    /etc/ansible/group_vars/raleigh
    /etc/ansible/group_vars/webservers
    /etc/ansible/host_vars/foosball

For instance, suppose you have hosts grouped by datacenter, and each datacenter
uses some different servers.  The data in the groupfile '/etc/ansible/group_vars/raleigh' for
the 'raleigh' group might look like::

    ---
    ntp_server: acme.example.org
    database_server: storage.example.org

It is ok if these files do not exist, this is an optional feature.

Tip: Keeping your inventory file and variables in a git repo (or other version control)
is an excellent way to track changes to your inventory and host variables.

.. versionadded:: 0.5
   If you ever have two python interpreters on a system, or your Python version 2 interpreter is not found
   at /usr/bin/python, set an inventory variable called 'ansible_python_interpreter' to the Python
   interpreter path you would like to use.

.. seealso::

   :doc:`examples`
       Examples of basic commands
   :doc:`playbooks`
       Learning ansible's configuration management language
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

