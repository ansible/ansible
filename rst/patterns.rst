.. _patterns:

The Inventory File, Patterns, and Groups
========================================

Ansible works against multiple systems in your infrastructure at the
same time.  It does this by selecting portions of systems listed in
Ansible's inventory file, which defaults to /etc/ansible/hosts.

.. _inventoryformat:

Inventory File Format
+++++++++++++++++++++

The format for /etc/ansible/hosts looks like this::

    mail.example.com

    [webservers]
    foo.example.com
    bar.example.com

    [dbservers]
    one.example.com
    two.example.com
    three.example.com

The things in brackets are group names, you don't have to have them,
but they are useful.

Selecting Targets
+++++++++++++++++

We'll go over how to use the command line in :doc:`examples` section, however, basically it looks like this::

    ansible <pattern_goes_here> -m <module_name> -a <arguments>
    
Such as::

    ansible webservers -m service -a "name=httpd state=restarted"

Within :doc:`playbooks`, these patterns can also be used, for even greater purposes.

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

Individual host names (or IPs), but not groups, can also be referenced using
wildcards::

    *.example.com
    *.com

It's also ok to mix wildcard patterns and groups at the same time::

    one*.com:dbservers

.. note::
    It is not possible to target a host not in the inventory file.   This is a safety feature.

Easy enough.  Now see :doc:`examples` and then :doc:`playbooks` for how to do things to selected hosts.

.. seealso::

   :doc:`examples`
       Examples of basic commands
   :doc:`playbooks`
       Learning ansible's configuration management language
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

