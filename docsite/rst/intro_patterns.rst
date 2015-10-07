Patterns
++++++++

.. index::
  pair: introduction; patterns

.. contents:: Topics

Patterns in Ansible are used in deciding which hosts to manage.  This can mean what hosts to communicate with, but in terms
of :doc:`playbooks` it actually means those hosts to which a particular configuration or IT process should be applied.

How to use the command line is covered in the :doc:`intro_adhoc` section, however, it basically looks like the following:

::

    ansible <pattern_goes_here> -m <module_name> -a <arguments>

Such as:

::

    ansible webservers -m service -a "name=httpd state=restarted"

A pattern usually refers to a set of groups, which are sets of hosts, and, in the above case, refers to systems assigned to the "webservers" group.

To use Ansible, you first must understand how to tell Ansible which hosts in your inventory to talk to, which is done by designating particular host names or groups of hosts.

The following set of patterns are equivalent and target all hosts in the inventory:

.. index::
  pair: patterns; target all hosts

::

    all
    *

It is also possible to address a specific host or set of hosts by name:

.. index:: 
  pair: patterns; specific host
  pair: patterns; hosts by name

::

    one.example.com
    one.example.com, two.example.com
    192.168.1.50
    192.168.1.*

The following patterns address one or more groups.  Groups separated by a colon indicate an "OR" configuration.
This means the host may be in either one group or the other:

.. index::
  pair: patterns; groups (one or more)

::

    webservers
    webservers,dbservers

You can exclude groups as well, for instance, all machines must be in the group "webservers" but not in the group "phoenix":

.. index::
  pair: patterns; excluding groups

::

    webservers,!phoenix

You can also specify the intersection of two groups.  This would mean the hosts must be in the group "webservers" and
the host must also be in the group "staging":

.. index:: 
  pair: patterns; intersection of two groups

::

    webservers,&staging

You can use combinations of the above example patterns:

.. index::
  pair: patterns; combinations

::

    webservers,dbservers,&staging,!phoenix

The above configuration means that "all machines in the groups 'webservers' and 'dbservers' are to be managed if they are in
the group 'staging' also, but the machines are not to be managed if they are in the group 'phoenix'." 

You can also use variables if you want to pass some group specifiers via the "-e" argument to ansible-playbook, but this
is uncommonly used:

.. index::
  pair: patterns; variables

::

    webservers,!{{excluded}},&{{required}}

You also do not have to manage by strictly defined groups.  Individual host names, IPs and groups, can also be referenced using
wildcards:

.. index::
  pair: patterns; wildcards

::

    *.example.com
    *.com

It's also ok to mix wildcard patterns and groups at the same time:

.. index::
  pair: patterns; combinations

::

    one*.com,dbservers

You can select a host or subset of hosts from a group by their position. For example, given the following group:

.. index::
  pair: patterns; host selection by position

::

    [webservers]
    cobweb
    webbing
    weber

You can refer to hosts within the group by adding a subscript to the group name:

.. index::
  pair: patterns; host reference with subscripts

::

    webservers[0]       # == cobweb
    webservers[-1]      # == weber
    webservers[0:1]     # == webservers[0],webservers[1]
                        # == cobweb,webbing
    webservers[1:]      # == webbing,weber

Most people do not specify patterns as regular expressions, but you can.  Just start the pattern with a ``~``:

.. index::
  pair: patterns; regular expressions

::

    ~(web|db).*\.example\.com

Additionally, you can add an exclusion criteria just by supplying the ``--limit`` flag to ``/usr/bin/ansible`` or ``/usr/bin/ansible-playbook``:

.. index::
  pair: patterns; exclusion criteria
  pair: patterns; --limit flag

::

    ansible-playbook site.yml --limit datacenter2

And if you want to read the list of hosts from a file, prefix the file name with ``@`` (available starting with Ansible v1.2):

.. index::
  pair: patterns; list of hosts (from file)
  pair: patterns; @ (reading host list from file)

::

    ansible-playbook site.yml --limit @retry_hosts.txt

Refer to :doc:`intro_adhoc` and then :doc:`playbooks` for more practical information in applying this knowledge.

.. seealso::

   :doc:`intro_adhoc`
       Examples of basic commands
   :doc:`playbooks`
       Learning ansible's configuration management language
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

