Patterns
++++++++

.. contents:: Topics

Patterns in Ansible are how we decide which hosts to manage.  This can mean what hosts to communicate with, but in terms
of :doc:`playbooks` it actually means what hosts to apply a particular configuration or IT process to.

We'll go over how to use the command line in :doc:`intro_adhoc` section, however, basically it looks like this::

    ansible <pattern_goes_here> -m <module_name> -a <arguments>

Such as::

    ansible webservers -m service -a "name=httpd state=restarted"

A pattern usually refers to a set of groups (which are sets of hosts) -- in the above case, machines in the "webservers" group.

Anyway, to use Ansible, you'll first need to know how to tell Ansible which hosts in your inventory to talk to.
This is done by designating particular host names or groups of hosts.

The following patterns are equivalent and target all hosts in the inventory::

    all
    *

It is also possible to address a specific host or set of hosts by name::

    one.example.com
    one.example.com:two.example.com
    192.168.1.50
    192.168.1.*

The following patterns address one or more groups.  Groups separated by a colon indicate an "OR" configuration.
This means the host may be in either one group or the other::

    webservers
    webservers:dbservers

You can exclude groups as well, for instance, all machines must be in the group webservers but not in the group phoenix::

    webservers:!phoenix

You can also specify the intersection of two groups.  This would mean the hosts must be in the group webservers and
the host must also be in the group staging::

    webservers:&staging

You can do combinations::

    webservers:dbservers:&staging:!phoenix

The above configuration means "all machines in the groups 'webservers' and 'dbservers' are to be managed if they are in
the group 'staging' also, but the machines are not to be managed if they are in the group 'phoenix' ... whew!

You can also use variables if you want to pass some group specifiers via the "-e" argument to ansible-playbook, but this
is uncommonly used::

    webservers:!{{excluded}}:&{{required}}

You also don't have to manage by strictly defined groups.  Individual host names, IPs and groups, can also be referenced using
wildcards::

    *.example.com
    *.com

It's also ok to mix wildcard patterns and groups at the same time::

    one*.com:dbservers

You can select a host or subset of hosts from a group by their position. For example, given the following group::

    [webservers]
    cobweb
    webbing
    weber

You can refer to hosts within the group by adding a subscript to the group name::

    webservers[0]       # == cobweb
    webservers[-1]      # == weber
    webservers[0:1]     # == webservers[0],webservers[1]
                        # == cobweb,webbing
    webservers[1:]      # == webbing,weber

Most people don't specify patterns as regular expressions, but you can.  Just start the pattern with a '~'::

    ~(web|db).*\.example\.com

While we're jumping a bit ahead, additionally, you can add an exclusion criteria just by supplying the ``--limit`` flag to /usr/bin/ansible or /usr/bin/ansible-playbook::

    ansible-playbook site.yml --limit datacenter2

And if you want to read the list of hosts from a file, prefix the file name with '@'.  Since Ansible 1.2::

    ansible-playbook site.yml --limit @retry_hosts.txt

Easy enough.  See :doc:`intro_adhoc` and then :doc:`playbooks` for how to apply this knowledge.

.. note:: With the exception of version 1.9, you can use ',' instead of ':' as a host list separator. The ',' is prefered specially when dealing with ranges and ipv6.
.. note:: As of 2.0 the ';' is deprecated as a host list separator.

.. seealso::

   :doc:`intro_adhoc`
       Examples of basic commands
   :doc:`playbooks`
       Learning ansible's configuration management language
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

