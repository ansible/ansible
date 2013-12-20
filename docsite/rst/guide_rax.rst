Rackspace Cloud Guide
=========================

.. contents::
   :depth: 3

.. _introduction:

Introduction
````````````

.. note:: This section of the documentation is under construction.
   We are in the process of adding more examples about all of the rax modules and how they work together.  Once complete, there will also be examples for Rackspace Cloud in `ansible-examples <http://github.com/ansible/ansible-examples/>`_.

Ansible contains a number of core modules for interacting with Rackspace Cloud.  The purpose of this
section is to explain how to put Ansible modules together (and use inventory scripts) to use Ansible in Rackspace Cloud context.

Requirements for the rax modules are minimal.  All of the modules require and are tested against pyrax 1.5 or higher. You'll need this Python module installed on the execution host.  pyrax is not currently available in many operating system package repositories, so you will likely need to install it via pip:

.. code-block:: bash

    $ pip install pyrax

The following steps will often execute outside the host loop, so it makes sense to add localhost to inventory.  Ansible
may not require this step in the future:

.. code-block:: ini

    [localhost]
    localhost ansible_connection=local

And in your playbook steps we'll typically be using the following pattern for provisioning steps:

.. code-block:: yaml

    - hosts: localhost
      connection: local
      gather_facts: False

.. _virtual_environment:

Virtual Environment
+++++++++++++++++++

Special considerations for running ansible within a python virtual environment need to be taken if pyrax is not installed globally.  Ansible assumes, unless otherwise instructed, that the python binary will live at /usr/bin/python.  This is done so via the interpret line in the modules, however when instructed using ansible_python_interpreter, ansible will use this specified path to the python binary.

This is required when pyrax is only installed within the virtual environment, due to the global python not having access to the virtual environments site-packages directory.  The previously mentioned inventory configuration for localhost would then look similar to:

.. code-block:: ini

    [localhost]
    localhost ansible_connection=local ansible_python_interpreter=/path/to/ansible_venv/bin/python

.. _provisioning:

Provisioning
````````````

The rax module provides the ability to provision instances within Rackspace Cloud.  Typically the provisioning task will be performed against your Ansible master server as a local_action statement.  

.. note::

   Authentication with the Rackspace-related modules is handled by either 
   specifying your username and API key as environment variables or passing
   them as module arguments.

Here is an example of provisioning a instance in ad-hoc mode mode:

.. code-block:: bash

    $ ansible localhost -m rax -a "name=awx flavor=4 image=ubuntu-1204-lts-precise-pangolin wait=yes" -c local

In a play, this might look like (assuming the parameters are held as vars):

.. code-block:: yaml

    tasks:
      - name: Provision a set of instances
        local_action:
            module: rax
            name: "{{ rax_name }}"
            flavor: "{{ rax_flavor }}"
            image: "{{ rax_image }}"
            count: "{{ rax_count }}"
            group: "{{ group }}"
            wait: yes
        register: rax

By registering the return its then possible to dynamically create a host group consisting of these new instances.  This facilitates performing configuration actions on the hosts immediately in a subsequent task:

.. code-block:: yaml

    - name: Add all instance public IPs to host group
      local_action:
          module: add_host 
          hostname: "{{ item.name }}"
          ansible_ssh_host: "{{ item.rax_accessipv4 }}"
          ansible_ssh_pass: "{{ item.rax_adminpass }}"
          groupname: raxhosts
      with_items: rax.success
      when: rax.action == 'create'

With the host group now created, a second play in your provision playbook might now have some configuration steps:

.. code-block:: yaml    

    - name: Configuration play
      hosts: raxhosts
      user: root
      gather_facts: true
      tasks:
        - name: Install NTP service
          apt: pkg=ntp cache_valid_time=86400 update_cache=yes
          
        - name: Check NTP service
          service: name=ntpd state=started

Rather than include configuration inline, you may also choose to just do it as a task include or a role.

The method above ties the configuration of a host with the provisioning step.  This isn't always ideal and leads us onto the next section.

.. _host_inventory:

Host Inventory
``````````````

Once your nodes are spun up, you'll probably want to talk to them again.  The best way to handle his is to use the rax inventory plugin.

Even for larger environments, you might have nodes spun up from other tools.  You don't have to use Ansible to spin up guests.  Once these are created and you wish to configure them, the Rackspace Cloud API can be used to return system grouping with the help of the rax inventory script. This script can be used to group resources by their eta data.  Utilizing meta data is highly recommended in rax and can provide an easy way to sort between host groups and roles.

There are several recommended ways to manage inventory for Rackspace.  The first is utilizing the ``rax.py`` inventory script and the second is utilizing a standard Ansible ini formatted inventory file.

.. _raxpy:

rax.py
++++++

Copy ``rax.py`` from ``plugins/inventory`` into your inventory directory.  You can specify credentials for ``rax.py`` utilizing the ``RAX_CREDS_FILE`` environment variable 

.. code-block:: bash

    $ RAX_CREDS_FILE=~/.raxpub ansible all -i rax.py -m setup

``rax.py`` also accepts a ``RAX_REGION`` environment variable, which can contain an individual region, or a comma separated list of regions.

For more information about the credentials file, see _`Credentials File`.

When using ``rax.py``, you will not have a 'localhost' defined in the inventory.  As mentioned previously, you will often be running most of these modules outside of the host loop, and will need 'localhost' defined.  The recommended way to do this, would be to create an ``inventory`` directory, and place both the ``rax.py`` script and a file containing ``localhost`` in it.  Executing ``ansible`` or ``ansible-playbook`` and specifying the ``inventory`` directory instead of an individual file, will cause ansible to evaluate each file in that directory for inventory.

.. code-block:: bash

    $ RAX_CREDS_FILE=~/.raxpub ansible all -i inventory/ -m setup

The ``rax.py`` inventory script will output information similar to the following information, which will be utilized for inventory and discoverable hostvars:

.. code-block:: json

    {
        "ORD": [
            "test"
        ],
        "_meta": {
            "hostvars": {
                "test": {
                    "ansible_ssh_host": "1.1.1.1",
                    "rax_accessipv4": "1.1.1.1",
                    "rax_accessipv6": "2607:f0d0:1002:51::4",
                    "rax_addresses": {
                        "private": [
                            {
                                "addr": "2.2.2.2",
                                "version": 4
                            }
                        ],
                        "public": [
                            {
                                "addr": "1.1.1.1",
                                "version": 4
                            },
                            {
                                "addr": "2607:f0d0:1002:51::4",
                                "version": 6
                            }
                        ]
                    },
                    "rax_config_drive": "",
                    "rax_created": "2013-11-14T20:48:22Z",
                    "rax_flavor": {
                        "id": "performance1-1",
                        "links": [
                            {
                                "href": "https://ord.servers.api.rackspacecloud.com/111111/flavors/performance1-1",
                                "rel": "bookmark"
                            }
                        ]
                    },
                    "rax_hostid": "e7b6961a9bd943ee82b13816426f1563bfda6846aad84d52af45a4904660cde0",
                    "rax_human_id": "test",
                    "rax_id": "099a447b-a644-471f-87b9-a7f580eb0c2a",
                    "rax_image": {
                        "id": "b211c7bf-b5b4-4ede-a8de-a4368750c653",
                        "links": [
                            {
                                "href": "https://ord.servers.api.rackspacecloud.com/111111/images/b211c7bf-b5b4-4ede-a8de-a4368750c653",
                                "rel": "bookmark"
                            }
                        ]
                    },
                    "rax_key_name": null,
                    "rax_links": [
                        {
                            "href": "https://ord.servers.api.rackspacecloud.com/v2/111111/servers/099a447b-a644-471f-87b9-a7f580eb0c2a",
                            "rel": "self"
                        },
                        {
                            "href": "https://ord.servers.api.rackspacecloud.com/111111/servers/099a447b-a644-471f-87b9-a7f580eb0c2a",
                            "rel": "bookmark"
                        }
                    ],
                    "rax_metadata": {
                        "foo": "bar"
                    },
                    "rax_name": "test",
                    "rax_name_attr": "name",
                    "rax_networks": {
                        "private": [
                            "2.2.2.2"
                        ],
                        "public": [
                            "1.1.1.1",
                            "2607:f0d0:1002:51::4"
                        ]
                    },
                    "rax_os-dcf_diskconfig": "AUTO",
                    "rax_os-ext-sts_power_state": 1,
                    "rax_os-ext-sts_task_state": null,
                    "rax_os-ext-sts_vm_state": "active",
                    "rax_progress": 100,
                    "rax_status": "ACTIVE",
                    "rax_tenant_id": "111111",
                    "rax_updated": "2013-11-14T20:49:27Z",
                    "rax_user_id": "22222"
                }
            }
        }
    }

.. _standard_inventory:

Standard Inventory
++++++++++++++++++

When utilizing a standard ini formatted inventory file, it may still be adventageous to retrieve discoverable hostvar information from the Rackspace API.  That can be achieved with the ``rax_facts`` module and an inventory file similar to the following:

.. code-block:: ini

    [test-servers]
    test rax_region=ORD

.. code-block:: yaml

    - name: Gather info about servers
      hosts: all
      gather_facts: False
      tasks:
        - name: Get facts about servers
          local_action:
            module: rax_facts
            credentials: ~/.raxpub
            name: "{{ inventory_hostname }}"
            region: "{{ rax_region }}"
        - name: Map some facts
          set_fact:
            ansible_ssh_host: "{{ rax_accessipv4 }}"

The ``rax_facts`` module will return the following JSON structure, providing hostvars/facts about the servers that matches the ``rax.py`` inventory script:

.. code-block:: json

    {
        "ansible_facts": {
            "rax_accessipv4": "1.1.1.1",
            "rax_accessipv6": "2607:f0d0:1002:51::4",
            "rax_addresses": {
                "private": [
                    {
                        "addr": "2.2.2.2",
                        "version": 4
                    }
                ],
                "public": [
                    {
                        "addr": "1.1.1.1",
                        "version": 4
                    },
                    {
                        "addr": "2607:f0d0:1002:51::4",
                        "version": 6
                    }
                ]
            },
            "rax_config_drive": "",
            "rax_created": "2013-11-14T20:48:22Z",
            "rax_flavor": {
                "id": "performance1-1",
                "links": [
                    {
                        "href": "https://ord.servers.api.rackspacecloud.com/111111/flavors/performance1-1",
                        "rel": "bookmark"
                    }
                ]
            },
            "rax_hostid": "e7b6961a9bd943ee82b13816426f1563bfda6846aad84d52af45a4904660cde0",
            "rax_human_id": "test",
            "rax_id": "099a447b-a644-471f-87b9-a7f580eb0c2a",
            "rax_image": {
                "id": "b211c7bf-b5b4-4ede-a8de-a4368750c653",
                "links": [
                    {
                        "href": "https://ord.servers.api.rackspacecloud.com/111111/images/b211c7bf-b5b4-4ede-a8de-a4368750c653",
                        "rel": "bookmark"
                    }
                ]
            },
            "rax_key_name": null,
            "rax_links": [
                {
                    "href": "https://ord.servers.api.rackspacecloud.com/v2/111111/servers/099a447b-a644-471f-87b9-a7f580eb0c2a",
                    "rel": "self"
                },
                {
                    "href": "https://ord.servers.api.rackspacecloud.com/111111/servers/099a447b-a644-471f-87b9-a7f580eb0c2a",
                    "rel": "bookmark"
                }
            ],
            "rax_metadata": {
                "foo": "bar"
            },
            "rax_name": "test",
            "rax_name_attr": "name",
            "rax_networks": {
                "private": [
                    "2.2.2.2"
                ],
                "public": [
                    "1.1.1.1",
                    "2607:f0d0:1002:51::4"
                ]
            },
            "rax_os-dcf_diskconfig": "AUTO",
            "rax_os-ext-sts_power_state": 1,
            "rax_os-ext-sts_task_state": null,
            "rax_os-ext-sts_vm_state": "active",
            "rax_progress": 100,
            "rax_status": "ACTIVE",
            "rax_tenant_id": "111111",
            "rax_updated": "2013-11-14T20:49:27Z",
            "rax_user_id": "22222"
        },
        "changed": false
    }

.. _credentials_file:

Credentials File
````````````````

The `rax.py` inventory script and all `rax` modules support a standard `pyrax` credentials file that looks like:

.. code-block:: ini

    [rackspace_cloud]
    username = myraxusername
    api_key = d41d8cd98f00b204e9800998ecf8427e

More information about this credentials file can be found at https://github.com/rackspace/pyrax/blob/master/docs/getting_started.md#authenticating

.. _use_cases:

Use Cases
`````````

This section covers some usage examples built around a specific use case.

.. _example_1:

Example 1
+++++++++

Create an isolated cloud network and build a server

.. code-block:: yaml
   
    - name: Build Servers on an Isolated Network
      hosts: localhost
      connection: local
      gather_facts: False
      tasks:
        - name: Network create request
          local_action:
            module: rax_network
            credentials: ~/.raxpub
            label: my-net
            cidr: 192.168.3.0/24
            region: IAD
            state: present
            
        - name: Server create request
          local_action:
            module: rax
            credentials: ~/.raxpub
            name: web%04d.example.org
            flavor: 2
            image: ubuntu-1204-lts-precise-pangolin
            disk_config: manual
            networks:
              - public
              - my-net
            region: IAD
            state: present
            count: 5
            exact_count: yes
            group: web
            wait: yes
            wait_timeout: 360
          register: rax

.. _example_2:

Example 2
+++++++++

Build a complete webserver environment with servers, custom networks and load balancers, install nginx and create a custom index.html

.. code-block:: yaml
   
    ---
    - name: Build environment
      hosts: localhost
      connection: local
      gather_facts: False
      tasks:
        - name: Load Balancer create request
          local_action:
            module: rax_clb
            credentials: ~/.raxpub
            name: my-lb
            port: 80
            protocol: HTTP
            algorithm: ROUND_ROBIN
            type: PUBLIC
            timeout: 30
            region: IAD
            wait: yes
            state: present
            meta:
              app: my-cool-app
          register: clb
    
        - name: Network create request
          local_action:
            module: rax_network
            credentials: ~/.raxpub
            label: my-net
            cidr: 192.168.3.0/24
            state: present
            region: IAD
          register: network
    
        - name: Server create request
          local_action:
            module: rax
            credentials: ~/.raxpub
            name: web%04d.example.org
            flavor: performance1-1
            image: ubuntu-1204-lts-precise-pangolin
            disk_config: manual
            networks:
              - public
              - private
              - my-net
            region: IAD
            state: present
            count: 5
            exact_count: yes
            group: web
            wait: yes
          register: rax
    
        - name: Add servers to web host group
          local_action:
            module: add_host
            hostname: "{{ item.name }}"
            ansible_ssh_host: "{{ item.rax_accessipv4 }}"
            ansible_ssh_pass: "{{ item.rax_adminpass }}"
            ansible_ssh_user: root
            groupname: web
          with_items: rax.success
          when: rax.action == 'create'
    
        - name: Add servers to Load balancer
          local_action:
            module: rax_clb_nodes
            credentials: ~/.raxpub
            load_balancer_id: "{{ clb.balancer.id }}"
            address: "{{ item.networks.private|first }}"
            port: 80
            condition: enabled
            type: primary
            wait: yes
            region: IAD
          with_items: rax.success
          when: rax.action == 'create'
    
    - name: Configure servers
      hosts: web
      handlers:
        - name: restart nginx
          service: name=nginx state=restarted
    
      tasks:
        - name: Install nginx
          apt: pkg=nginx state=latest update_cache=yes cache_valid_time=86400
          notify:
            - restart nginx
    
        - name: Ensure nginx starts on boot
          service: name=nginx state=started enabled=yes
    
        - name: Create custom index.html
          copy: content="{{ inventory_hostname }}" dest=/usr/share/nginx/www/index.html
                owner=root group=root mode=0644


.. _advanced_usage:

Advanced Usage
``````````````
.. _awx_autoscale:

AWX Autoscaling
+++++++++++++++

AnsibleWorks's "AWX" product also contains a very nice feature for auto-scaling use cases.  In this mode, a simple curl script can call a defined URL and the server will "dial out" to the requester and configure an instance that is spinning up.  This can be a great way to reconfigure ephmeral nodes.  See the AWX documentation for more details.  Click on the AWX link in the sidebar for details.

A benefit of using the callback in AWX over pull mode is that job results are still centrally recorded and less information has to be shared with remote hosts.


.. _pending_information:

Pending Information
```````````````````

More to come