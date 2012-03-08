Patterns
========

How to select hosts you wish to manage

.. seealso::

   :doc:`examples`
       Examples of basic commands
   :doc:`playbooks`
       Learning ansible's configuration management language

Ansible works against multiple systems in your infrastructure at the
same time.  It does this by selecting portions of systems listed in Ansible's inventory file,
which defaults to /etc/ansible/hosts, and looks like this::

    mail.example.com

    [webservers]
    foo.example.com
    bar.example.com

    [dbservers]
    one.example.com
    two.example.com
    three.example.com

Targetting All Systems
``````````````````````

The pattern 'all' or '*' targets all systems in the inventory file.   
   
Specific Hosts
``````````````

It is possible to address specific hosts:

    one.example.com
    one.example.com:two.example.com
 
Groups
``````

The following patterns address one or more groups:

    webservers
    webservers:dbservers

There is also a magic group 'ungrouped' which selects systems not in a group.
    
Wildcards
`````````

Individual hosts, but not groups, can also be referenced using wildcards:

    *.example.com
    *.com

Mixing Things Up
````````````````

Specific hosts, wildcards, and groups can all be mixed in the same pattern

   one*.com:dbservers

It is not possible to target a host not in the inventory file.



