================
Python 3 Support
================

Ansible 2.2 features a tech preview of Python 3 support. This topic discusses how you can test to make sure your modules and playbooks work with Python 3.


.. note:: Technology preview features provide early access to upcoming product innovations, 
   enabling you to test functionality and provide feedback during the development process.
   Please be aware that tech preview features may not be functionally complete and are not    
   intended for production use. To report a Python 3 bug, please see `Community Information & Contributing <http://docs.ansible.com/ansible/community.html#i-d-like-to-report-a-bug>`_.

Testing Python 3 with commands and playbooks
----------------------------------------------------

* `Install Ansible 2.2+ <http://docs.ansible.com/ansible/intro_installation.html>`_
* To test Python 3 on the controller, run your ansible command via
  `python3`. For example::


    $ python3 /usr/bin/ansible localhost -m ping
    $ python3 /usr/bin/ansible-playbook sample-playbook.yml


Testing Python 3 module support
--------------------------------

* Set the ansible_python_interpreter configuration option to
  `/usr/bin/python3`. The `ansible_python_interpreter` configuration option is usually set per-host as inventory variable associated with a host or set of hosts. See the `inventory documentation <http://docs.ansible.com/ansible/intro_inventory.html>`_ for more information. 
* Run your command or playbook.::

    $ ansible localhost -m ping 
    $ ansible-playbook sample-playbook.yml


Note that you can also use the `-e` command line option to manually set the python interpreter when you run a command. For example::  
  
  $ ansible localhost -m ping -e 'ansible_python_interpreter=/usr/bin/python3'
  $ ansible-playbook sample-playbook.yml -e 'ansible_python_interpreter=/usr/bin/python3'

