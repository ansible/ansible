.. _patterns:

The Inventory File, Patterns, and Groups
========================================

Ansible works against multiple systems in your infrastructure at the
same time.  It does this by selecting portions of systems listed in
Ansible's inventory file, which defaults to /etc/ansible/hosts.

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
after the hostname with a colon.  

    four.example.com:5309

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

Individual host names (or IPs), but not groups, can also be referenced using
wildcards::

    *.example.com
    *.com

It's also ok to mix wildcard patterns and groups at the same time::

    one*.com:dbservers

.. note::
    It is not possible to target a host not in the inventory file, unless using playbooks with --override-hosts.  More on that later.  This is a safety feature.

Easy enough.  See :doc:`examples` and then :doc:`playbooks` for how to do things to selected hosts.

Host Variables
++++++++++++++

Using the 0.4 branch of Ansible, it is easy to assign variables to hosts that will be used
later in playbooks::
 
   [atlanta]
   host1 http_port=80 maxRequestsPerChild=808
   host2 http_port=303 maxRequestsPerChild=909


Group Variables
+++++++++++++++

Using the 0.4 branch of Ansible, variables can also be applied to an entire group at once::

   [atlanta]
   host1
   host2

   [atlanta:vars]
   ntp_server=ntp.atlanta.example.com
   proxy=proxy.atlanta.example.com

Groups of Groups
++++++++++++++++

Using the 0.4 branch of Ansible, it is possible to make groups of groups::

   [atlanta]
   host1
   host2

   [raleigh]
   host2
   host3

   [southeast:children]
   alpha
   beta

   [southeast:vars]
   some_server=foo.southeast.example.com

   [usa:children]
   southeast
   northeast
   southwest
   southeast

YAML Inventory Format
+++++++++++++++++++++

For people using 0.3, or those that prefer to use it, the inventory file can also be expressed in
YAML::

    ---
    
    # some ungrouped hosts, either use the short string form or the "host: " prefix
    - host: jupiter
    - mars

    # variables can be assigned like this...
    - host: saturn
      vars:
      - moon: titan

    # groups can also set variables to all hosts in the group
    # here are a bunch of hosts using a non-standard SSH port
    # and also defining a variable 'ntpserver'
    - group: greek
      hosts:
      - zeus
      - hera
      - poseidon
      vars:
      - ansible_ssh_port: 3000
      - ntp_server: olympus.example.com

    # individual hosts can still set variables inside of groups too
    # so you aren't limited to just group variables and host variables.
    - group: norse
      hosts:
      - host: thor
        vars:
        - hammer: True
      - odin
      - loki
      vars:
        - asdf: 1234

Tip: Be sure to start your YAML file with the YAML record designator ``---``.

.. seealso::

   :doc:`examples`
       Examples of basic commands
   :doc:`playbooks`
       Learning ansible's configuration management language
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

