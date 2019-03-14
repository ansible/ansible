.. _quickstart_guide:

Ansible Quickstart Guide
========================

We've recorded a short video that introduces Ansible.

The `quickstart video <https://www.ansible.com/resources/videos/quick-start-video>`_ is about 13 minutes long and gives you a high level
introduction to Ansible -- what it does and how to use it. We'll also tell you about other products in the Ansible ecosystem.

Or if you prefer, follow along in this document for a quick introduction to Ansible.

.. contents::
   :local:

Installing Ansible
------------------
Ansible by default manages machines over the SSH protocol.

Once Ansible is installed, it will not add a database, and there will be no daemons to start or keep running. You only need to install it on one machine (the *control node*, which could easily be a laptop) and it can manage an entire fleet of remote machines from that central point.

To install Ansible on a Fedora or CentOS control node:

.. code-block:: bash

   sudo yum install ansible

See the :ref:`installation_guide` for complete installation instructions for other operating systems.

Creating an inventory file
--------------------------
Ansible works against multiple systems in your infrastructure at the same time.
It does this by selecting portions of systems listed in Ansible's inventory,
which defaults to being saved in the location ``/etc/ansible/hosts``.
You can specify a different inventory file using the ``-i <path>`` option on the command line.

To create a simple inventory file in YAML format for three systems:

.. code-block:: yaml

   ---
   all:
     children:
       webservers:
         hosts:
           foo.example.com:
           bar.example.com:
       dbservers:
         hosts:
           one.example.com:

This example groups the systems into *webservers* and *dbservers*. Groups allow you to run different playbooks against a group of related systems.

You can use an Ansible :ref:`ad-hoc command <intro_adhoc>` to verify connectivity to your inventory:

.. code-block:: bash

  $ ansible all -m ping

    foo.example.com | SUCCESS => {
       "changed": false,
       "failed": false,
       "ping": "pong"
    }
    bar.example.com | SUCCESS => {
       "changed": false,
       "failed": false,
       "ping": "pong"
    }
    one.example.com | SUCCESS => {
       "changed": false,
       "failed": false,
       "ping": "pong"
    }

See :ref:`intro_inventory` for more details on creating and using inventory files.

Creating your first playbook
----------------------------

Create your first playbook, using the ``yum`` ``template`` and ``service`` module. Modules in Ansible are the building blocks you use to develop tasks:

.. code-block:: yaml

    ---
    - name: Install nginx
      hosts: webservers
      become: true

      tasks:
      - name: Add epel-release repo
        yum:
          name: epel-release
          state: present

      - name: Install nginx
        yum:
          name: nginx
          state: present

      - name: Insert Index Page
        template:
          src: index.html
          dest: /usr/share/nginx/html/index.html

      - name: Start NGiNX
        service:
          name: nginx
          state: started

Verifying your playbook
-----------------------

You have three ways you can quickly verify your playbook:
* Run the playbook with --check:

  .. code-block:: bash

    <code>

* Install ansible-lint and run this against your playbook:

  .. code-block:: bash

    <code>

* Run the playbook with -v (or -vvvv) to display deeper levels of debugging invormation. This approach will actually run the playbook against the simple inventory we created earler:

  .. code-block:: bash

    <code>


Tips on where to go next
------------------------


Enjoy, and be sure to visit the rest of the documentation to learn more.
