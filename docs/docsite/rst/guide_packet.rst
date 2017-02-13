Using Ansible with the Packet host
==================================

Introduction
------------

`Packet.net <https://packet.net>`_ is a bare metal infrastructure host. Ansible (>=2.3) ships with several components which can be used for provisioning in Packet: a dynamic inventory script and two cloud modules.

This guide shows how to manage devices in Packet infrastructure with Ansbile. There are two modules:

    packet_sshkey
        Adds a public SSH key from file or value to the Packet infrastructure. Every subsequently-created device will have this public key installed in .ssh/authorized_keys.

    packet_device
        Manages devices (hardware servers) in the Packet infrastructure. You can use this module to create, restart and delete devices.


Requirements
------------

The Packet modules and inventory connect to the Packet API using the packet-python package. You can install it with pip:

.. code-block:: bash

    $ pip install packet-python 

In order to check state of devices created by Ansible in Packet, it's a good idea to install one of the `Packet CLI clients <https://www.packet.net/developers/integrations/api-cli/>`_. 

The modules and the inventory also need to authenticate you in Packet via an API token. You can generate API token in `here <https://app.packet.net/portal#/api-keys>`_. The simplest way is to pass your Packet API token in an envrionment variable: 

.. code-block:: bash

    $ export PACKET_API_TOKEN=Bfse9F24SFtfs423Gsd3ifGsd43sSdfs

If you are not comfortable exporting your API token, you can pass it as a parameter to the modules.

In the Packet infrastructure, devices and reserved IP addresses belong to a single `project <https://www.packet.net/developers/api/projects/>`_. In order to use the packet_device module, you need to specify the UUID of the project in which you want to create the devices. You can find it out from the `project listing <https://app.packet.net/portal#/projects/list/table>`_, it's just under the project table. Alternatively, you can see the UUIDs of your projects via some CLI.


If you want to use a new SSH keypair in this tutorial, you can generate it to ``./id_rsa`` and ``./id_rsa.pub`` as:

.. code-block:: bash

    $ ssh-keygen -t rsa -f ./id_rsa

If you want to use existing keypair, just copy the private and public key over to the playbook directory.



Single device creation and removal
----------------------------------

Following code block is a simple playbook creating one ubuntu_16_04 device. You have to supply ``plan`` and ``operating_system``. ``location`` defaults to ``ewr1`` (Parsippany, NJ). You can find all the possible values for the parametets via a CLI client.

.. code-block:: yaml

    # playbook_create.yml

    - name: create ubuntu device
      hosts: localhost
      tasks:

      - packet_sshkey:
          key_file: ./id_rsa.pub
          label: tutorial key

      - packet_device:
          project_id: <your_project_id>
          hostnames: myserver
          operating_system: ubuntu_16_04
          plan: baremetal_0
          facility: sjc1

After

.. code-block:: bash

    $ ansible-playbook playbook_create.yml
    
you should have a device created in the Packet host. Feel free to verify with CLI tools of your choice or in the `web dashboard <https://app.packet.net/portal#/projects/list/table>`_.

If you got an error with message "failed to set machine state present, error: Error 404: Not Found", please verify that you set the project_id in the playbook to your actual project UUID.

Allocated devices are reported to be "provisioning" by the API for a few minutes, during which any modifying API call will result in 422-Unprocessable-Entity response. Take a short break and get back to this tutorial once your new "myserver" device is reported "active" by the API.

The packet_device module has a "state" parameter. Its possible values are: active (the default), inactive (powered-off), rebooted and absent. If your playbook acts on existing devices, you can only pass a hostname or device_ids parameters which uniquely specify a device (or a list of devices). For illustration, if you'd like to reboot a device called "myserver", you can use following playbook.

.. code-block:: yaml

    # playbook_reboot.yml

    - name: reboot myserver
      hosts: localhost
      tasks:

      - packet_device:
          project_id: <your_project_id>
          hostnames: myserver
          state: rebooted
 
Note that the module call doesn't specify plan or facility.

Instead of hostnames, you can also refer to devices with device_ids. Please find out the UUID of the "myserver" device (via web console, or a cli client), and fill it in following playbook:

.. code-block:: yaml

    # playbook_remove.yml

    - name: remove a device
      hosts: localhost
      tasks:

      - packet_device:
          project_id: <your_project_id>
          device_ids: <myserver_device_id> 
          state: absent

After 

.. code-block:: bash

    $ ansible-playbook playbook_remove.yml`` 

you should not see the device in the project listing.

Specifying devices
------------------

The two arguments used to uniquely refer to devices are in plural form: "device_ids" and "hostnames". It's because the module will accept both string (later converted to one-element list), or a list of strings for these arguments.

The device_ids and the hostnames parameters are mutually exclusive. These are all acceptable arguments for the module:

- device_ids: a27b7a83-fc93-435b-a128-47a5b04f2dcf

- hostnames: mydev1

- device_ids: [a27b7a83-fc93-435b-a128-47a5b04f2dcf, 4887130f-0ccd-49a0-99b0-323c1ceb527b]

- hostnames: [mydev1, mydev2]

In addition, hostnames can contain the %d formatter, which will be expanded numbers from range of the count parameter. E.g. hostnames: "mydev%d", count: 2; will expand the hostnames to [mydev1, mydev2].


More complex playbook
---------------------

In a more complex scenario, we will create a CoreOS cluster with specified metadata.


The CoreOS is using etcd (distributed key-value storage) for discovery of other nodes in a cluster. Without assumptions on existing resources, we use public etcd service for discovery of nodes in our new cluster. Before starting the devices, we need to generate discovery token for our cluster:

.. code-block:: bash

    $ curl -w "\n" 'https://discovery.etcd.io/new?size=3'

Following playbook will create the SSH key, create the nodes and then wait until SSH is ready (or until 5 minutes passed). Please substitute the discovery token url in the CoreOS userdata, and the project_id before running ansible-playbook. Also, feel free to change the plan and facility.

.. code-block:: yaml

    # playbook_coreos.yml

    - name: Start 3 CoreOS nodes in Packet and wait until SSH is ready
      hosts: localhost
      tasks:

      - packet_sshkey:
          key_file: ./id_rsa.pub
          label: new

      - packet_device:
          hostnames: [coreos-one, coreos-two, coreos-three]
          operating_system: coreos_beta
          plan: baremetal_0
          facility: ewr1
          project_id: <your_project_id>
          wait: true
          user_data: |
            #cloud-config
            coreos:
              etcd2:
                discovery: https://discovery.etcd.io/<token>
                advertise-client-urls: http://$private_ipv4:2379,http://$private_ipv4:4001
                initial-advertise-peer-urls: http://$private_ipv4:2380
                listen-client-urls: http://0.0.0.0:2379,http://0.0.0.0:4001
                listen-peer-urls: http://$private_ipv4:2380
              fleet:
                public-ip: $private_ipv4
              units:
                - name: etcd2.service
                  command: start
                - name: fleet.service
                  command: start
        register: newhosts

      - name: wait for ssh
        wait_for:
          delay: 1
          host: "{{ item.public_ipv4 }}"
          port: 22
          state: started
          timeout: 500
        with_items: "{{ newhosts.devices }}"


As with most of the Ansible modules, the default states of the Packet modules are idempotent, i.e. the resources in your project will remain the same after multiple calls (re-runs of a playbook) of modules with unspecified state. Thus, we can keep the packet_sshkey module call in our playbook even when we have already uploaded it in the previous section. If the public key is already in your Packet account, the call will have no effect.

The second module call creates 3 devices (as there are 3 items in the hostnames parameter list) in given project. The "operating_system" is CoresOS beta, which can be customized with cloud-config user data. The packet_device module takes string for user data in the "user_data" parameter. It is in turn a YAML document containing a dictionary, but in context of this playbook, it must be (ideally multiline) string.

The packet_device module has boolean "wait" parameter with False as default. If set to True, Ansible will wait until the GET API call for a device will contain an Internet-routeable IP address. The IP address (IPv4) is then registed as "newhosts" (list) and used in the wait_for module call to poll port 22 (hopefully sshd) of the new device. IP address is assigned quite quickly to a new device, however the response for the creating POST doesn't contain it yet. The "wait" parameter allows us to use the IP address of the device as soon as it's available.

Run 

.. code-block:: bash

    $ ansible-playbook playbook_coreos.yml

and wait until the playbook quits. Your new devices should be reachable by SSH now. Try to connect to one and check if etcd has started properly:

.. code-block:: bash

    tomk@work $ ssh -i id_rsa core@<one_of_the_servers_ip>
    core@coreos-one ~ $ etcdctl cluster-health

Once you create a couple of devices, you might appreciate the dynamic inventory script.


Dynamic Inventory Script
------------------------

The dynamic inventory script queries Packet API for list of hosts, and exposes it to Ansible. You can find it in Ansible git repo in `contrib/inventory/packet_net.py <https://github.com/ansible/ansible/blob/devel/contrib/inventory/packet_net.py>`_. The inventory is configurable from an `ini file <https://github.com/ansible/ansible/blob/devel/contrib/inventory/packet_net.ini>`_. If you want to use the inventory script, you must first export your Packet API token to PACKET_API_TOKEN environment variable.

You can either copy the inventory and ini config out from the cloned git repo, or you can download it to working directory as:

.. code-block:: bash

    $ wget https://github.com/ansible/ansible/raw/devel/contrib/inventory/packet_net.py
    $ chmod +x packet_net.py
    $ wget https://github.com/ansible/ansible/raw/devel/contrib/inventory/packet_net.ini

In order to understand what the inventory script gives to Ansible you can run:

.. code-block:: bash

    $ ./packet_net.py --list

It should print a JSON document looking similar to following trimmed dictionary:

.. code-block:: json

    {
      "_meta": {
        "hostvars": {
          "147.75.64.169": {
            "packet_billing_cycle": "hourly", 
            "packet_created_at": "2017-02-09T17:11:26Z", 
            "packet_facility": "ewr1", 
            "packet_hostname": "coreos-two", 
            "packet_href": "/devices/d0ab8972-54a8-4bff-832b-28549d1bec96", 
            "packet_id": "d0ab8972-54a8-4bff-832b-28549d1bec96", 
            "packet_locked": false, 
            "packet_operating_system": "coreos_beta", 
            "packet_plan": "baremetal_0", 
            "packet_state": "active", 
            "packet_updated_at": "2017-02-09T17:16:35Z", 
            "packet_user": "core", 
            "packet_userdata": "#cloud-config\ncoreos:\n  etcd2:\n    discovery: https://discovery.etcd.io/e0c8a4a9b8fe61acd51ec599e2a4f68e\n    advertise-client-urls: http://$private_ipv4:2379,http://$private_ipv4:4001\n    initial-advertise-peer-urls: http://$private_ipv4:2380\n    listen-client-urls: http://0.0.0.0:2379,http://0.0.0.0:4001\n    listen-peer-urls: http://$private_ipv4:2380\n  fleet:\n    public-ip: $private_ipv4\n  units:\n    - name: etcd2.service\n      command: start\n    - name: fleet.service\n      command: start"
          }
        }
      }, 
      "baremetal_0": [
        "147.75.202.255", 
        "147.75.202.251", 
        "147.75.202.249", 
        "147.75.64.129", 
        "147.75.192.51", 
        "147.75.64.169"
      ], 
      "coreos_beta": [
        "147.75.202.255", 
        "147.75.202.251", 
        "147.75.202.249", 
        "147.75.64.129", 
        "147.75.192.51", 
        "147.75.64.169"
      ], 
      "ewr1": [
        "147.75.64.129", 
        "147.75.192.51", 
        "147.75.64.169"
      ], 
      "sjc1": [
        "147.75.202.255", 
        "147.75.202.251", 
        "147.75.202.249"
      ],
      "coreos-two": [
        "147.75.64.169"
      ],
      "d0ab8972-54a8-4bff-832b-28549d1bec96": [
        "147.75.64.169"
      ], 
    }

In the ``['_meta']['hostvars']`` key, there is a list of devices (uniquely identified by their public IPv4 address) with their parameters. The other keys under ``['_meta']`` are lists of devices grouped by some paramter. Here, it is type (all devices are of type baremetal_0), operating system, and facility (ewr1 and sjc1).

In addition to the parameter groups, there are also one-item groups with UUID or hostname of the device, enabling to refer to device by their hostnames.

You can now use the device hostnames in playbooks. Following playbook will install role supplying resources for Ansible target, into all devices in the "coreos_beta" group:

.. code-block:: yaml

    # plabyook_bootstrap.yml

    - hosts: coreos_beta
      gather_facts: false
      roles:
        - defunctzombie.coreos-boostrap

Don't forget to supply the dynamic inventory in the ``-i`` argument.

.. code-block:: bash

    $ ansible-playbook -u core -i packet_net.py playbook_bootstrap.yml


