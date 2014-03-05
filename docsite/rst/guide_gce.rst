 Google Cloud Platform Guide
============================

.. _gce_intro:

Introduction
------------

.. note:: This section of the documentation is under construction. We are in the process of adding more examples about all of the GCE modules and how they work together.

The GCE modules require the apache-libcloud module, which you can install from pip:

.. code-block:: bash

    $ pip install apache-libcloud

.. note:: If you're using Ansible on Mac OS X, libcloud needs to access a CA cert chain. You'll need to download one (you can get one for `here <http://curl.haxx.se/docs/caextract.html>`_.)

Credentials
-----------

To work with the GCE modules, you'll first need to get some credentials. You can create new one from the `console <https://console.developers.google.com/>`_ by going to the "APIs and Auth" section. Once you've created a new client ID and downloaded the generated private key (in the `pkcs12 format <http://en.wikipedia.org/wiki/PKCS_12>`_), you'll need to convert the key by running the following command:

.. code-block:: bash

    $ openssl pkcs12 -in pkey.pkcs12 -passin pass:notasecret -nodes -nocerts | openssl rsa -out pkey.pem

There's three different ways to provide credentials to Ansible when you want to talk to Google Cloud:

* by providing to the modules directly
* by populating a ``secrets.py`` file
* by populating the ``gce.ini`` file (for the inventory script only)

Module
``````

For the GCE modules you can specify the credentials as argument:

* ``service_account_email``: email associated with the project
* ``pem_file``: path to the pem file
* ``project_id``: id of the project

For example, to create a new instance using the cloud module, you can use the following configuration:

.. code-block:: yaml
   - name: Create instance(s)
     hosts: localhost
     gather_facts: no
     vars:
       service_account_email: unique-id@developer.gserviceaccount.com
       pem_file: /path/to/project.pem
       project_id: project-id
       machine_type: n1-standard-1
       image: debian-7
     tasks:
      - name: Launch instances
        local_action: gce instance_names=dev machine_type={{ machine_type }} image={{ image }} service_account_email={{ service_account_email }} pem_file={{ pem_file }} project_id={{ project_id }}

secrets.py
``````````

Create a file ``secrets.py`` looking like following, and put it in some folder which is in your ``$PYTHONPATH``:

.. code-block:: python

    GCE_PARAMS = ('i...@project.googleusercontent.com', '/path/to/project.pem')
    GCE_KEYWORD_PARAMS = {'project': 'project-name'}

gce.ini
```````

When using the inventory script ``gce.py``, you need to populate the ``gce.ini`` file that you can find in the inventory directory.

Host Inventory
--------------

The best way to interact with your hosts is to use the gce inventory plugin, which dynamically queries GCE and tells Ansible what nodes can be managed.

gce.py
++++++

To use the GCE dynamic inventory script, copy ``gce.py`` from ``plugings/inventory`` into your inventory directory and make it executable. You can specify credentials for ``gce.py`` using the ``GCE_INI_PATH`` environment variable.

Let's test our inventory script to see if it can talk to Google Cloud.

.. code-block:: bash

    $ GCE_INI_PATH=~/.gce.ini ansible all -i gce.py -m setup
    hostname | success >> {
      "ansible_facts": {
        "ansible_all_ipv4_addresses": [
          "x.x.x.x"
        ],

The recommended way to use the inventory is to create an ``inventory`` directory, and place both the ``gce.py`` script and a file containing ``localhost`` in it.

Executing ``ansible`` or ``ansible-playbook`` and specifying the ``inventory`` directory instead of an individual file will cause ansible to evaluate each file in that directory for inventory.

Let's test our inventory script to see if it can talk to Google Cloud:

.. code-block:: bash

    $ ansible all -i inventory/ -m setup
    hostname | success >> {
      "ansible_facts": {
        "ansible_all_ipv4_addresses": [
            "x.x.x.x"
        ],

The output should be similar to the previous command.

Use Cases
---------

For the following use case, I'm using a small shell script as a wrapper.

.. code-block:: bash

  #!/bin/bash
  PLAYBOOK="$1"

  if [ -z $PLAYBOOK ]; then
    echo "You need to pass a playback as argument to this script."
    exit 1
  fi

  export SSL_CERT_FILE=$(pwd)/cacert.cer
  export ANSIBLE_HOST_KEY_CHECKING=False

  if [ ! -f "$SSL_CERT_FILE" ]; then
    curl -O http://curl.haxx.se/ca/cacert.pem
  fi

  ansible-playbook -v -i inventory/ "$PLAYBOOK"


Create an instance
``````````````````

The GCE module provides the ability to provision instances within Google Compute Engine. The provisioning task is typically performed from your Ansible control server against Google Cloud's API.

A playbook would looks like this:

.. code-block:: yaml

   - name: Create instance(s)
     hosts: localhost
     gather_facts: no
     vars:
       machine_type: n1-standard-1 # default
       image: debian-7
       service_account_email: unique-id@developer.gserviceaccount.com
       pem_file: /path/to/project.pem
       project_id: project-id
     tasks:
       - name: Launch instances
         local_action: gce instance_names=dev machine_type={{ machine_type }} image={{ image }} service_account_email={{ service_account_email }} pem_file={{ pem_file }} project_id={{ project_id }}
      register: gce
      - name: Wait for SSH to come up
        local_action: wait_for host={{ item.public_ip }} port=22 delay=10 timeout=60 state=started
        with_items: gce.instance_data

Create a web server
```````````````````

With this example we will install a web server (lighttpd) on our new instance and ensure that the port 80 is open for incoming connections.

.. code-block:: yaml

  - name: Create a firewall rule to allow HTTP
    hosts: dev
    gather_facts: no
    vars:
      machine_type: n1-standard-1 # default
      image: debian-7
      service_account_email: unique-id@developer.gserviceaccount.com
      pem_file: /path/to/project.pem
      project_id: project-id
    tasks:
      - name: Install lighttpd
        apt: pkg=lighttpd state=installed
        sudo: True
      - name: Allow HTTP
        local_action: gce_net fwname=all-http name=default allowed=tcp:80 state=present service_account_email={{ service_account_email }} pem_file={{ pem_file }} project_id={{ project_id }}

By pointing your browser to the IP of the server, you should see a page welcoming you.
