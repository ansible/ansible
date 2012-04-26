.. _patterns:

The Inventory File, Patterns, and Groups
========================================

Ansible works against multiple systems in your infrastructure at the
same time.  It does this by selecting portions of systems listed in
Ansible's inventory file, which defaults to /etc/ansible/hosts.

.. _inventoryformat:

Basic Inventory File Format
+++++++++++++++++++++++++++

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

If you have hosts that run on non-standard SSH ports you can put the port number
after the hostname with a colon.  This requires Ansible 0.3 (integration branch)::

    four.example.com:5309

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

Easy enough.  See :doc:`examples` and then :doc:`playbooks` for how to do things to selected hosts.

Advanced Inventory File Format
++++++++++++++++++++++++++++++

(This features requires the integration branch of Ansible, soon to be release 0.3)

Once you read about playbooks you'll quickly see how useful it will be to assign particular variables
to particular hosts and groups of hosts.  While the default INI-style host format doesn't allow this,
switching to the YAML inventory format can add some compelling capabilities.  Just replace your INI
style file with a YAML one.::

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

Tip: Be sure to start your YAML file with the YAML record designator "---".

NOTE: variables specified in playbooks will override variables specified
in the host file.  Further, if a host is in multiple groups, currently, the
variables set by the last loaded group will win over variables set in other
groups.  This behavior may be refined in future releases.

.. seealso::

   :doc:`examples`
       Examples of basic commands
   :doc:`playbooks`
       Learning ansible's configuration management language
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

