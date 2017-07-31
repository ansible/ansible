Google Cloud Platform Guide
===========================

.. gce_intro:

Introduction
------------

.. note:: This section of the documentation is under construction. We are in the process of adding more examples about all of the GCE modules and how they work together. Upgrades via github pull requests are welcomed!

Ansible contains modules for managing Google Compute Engine resources, including creating instances, controlling network access, working with persistent disks, and managing
load balancers.  Additionally, there is an inventory plugin that can automatically suck down all of your GCE instances into Ansible dynamic inventory, and create groups by tag and other properties.

The GCE modules all require the apache-libcloud module which you can install from pip:

.. code-block:: bash

    $ pip install apache-libcloud

.. note:: If you're using Ansible on Mac OS X, libcloud also needs to access a CA cert chain. You'll need to download one (you can get one for `here <http://curl.haxx.se/docs/caextract.html>`_.)

Credentials
-----------

To work with the GCE modules, you'll first need to get some credentials in the
JSON format:

1. `Create a Service Account <https://developers.google.com/identity/protocols/OAuth2ServiceAccount#creatinganaccount>`_
2. `Download JSON credentials <https://support.google.com/cloud/answer/6158849?hl=en&ref_topic=6262490#serviceaccounts>`_

There are three different ways to provide credentials to Ansible so that it can talk with Google Cloud for provisioning and configuration actions:

.. note:: If you would like to use JSON credentials you must have libcloud >= 0.17.0

* by providing to the modules directly
* by populating a ``secrets.py`` file
* by setting environment variables

Calling Modules By Passing Credentials
``````````````````````````````````````

For the GCE modules you can specify the credentials as arguments:

* ``service_account_email``: email associated with the project
* ``credentials_file``: path to the JSON credentials file
* ``project_id``: id of the project

For example, to create a new instance using the cloud module, you can use the following configuration:

.. code-block:: yaml

   - name: Create instance(s)
     hosts: localhost
     connection: local
     gather_facts: no

     vars:
       service_account_email: unique-id@developer.gserviceaccount.com
       credentials_file: /path/to/project.json
       project_id: project-id
       machine_type: n1-standard-1
       image: debian-7

     tasks:

      - name: Launch instances
        gce:
            instance_names: dev
            machine_type: "{{ machine_type }}"
            image: "{{ image }}"
            service_account_email: "{{ service_account_email }}"
            credentials_file: "{{ credentials_file }}"
            project_id: "{{ project_id }}"

When running Ansible inside a GCE VM you can use the service account credentials from the local metadata server by
setting both ``service_account_email`` and ``credentials_file`` to a blank string.

Configuring Modules with secrets.py
```````````````````````````````````

Create a file ``secrets.py`` looking like following, and put it in some folder which is in your ``$PYTHONPATH``:

.. code-block:: python

    GCE_PARAMS = ('i...@project.googleusercontent.com', '/path/to/project.json')
    GCE_KEYWORD_PARAMS = {'project': 'project_id'}

Ensure to enter the email address from the created services account and not the one from your main account.

Now the modules can be used as above, but the account information can be omitted.

If you are running Ansible from inside a GCE VM with an authorized service account you can set the email address and
credentials path as follows so that get automatically picked up:

.. code-block:: python

    GCE_PARAMS = ('', '')
    GCE_KEYWORD_PARAMS = {'project': 'project_id', 'datacenter': ''}

Configuring Modules with Environment Variables
``````````````````````````````````````````````

Set the following environment variables before running Ansible in order to configure your credentials:

.. code-block:: bash

    GCE_EMAIL
    GCE_PROJECT
    GCE_CREDENTIALS_FILE_PATH

GCE Dynamic Inventory
---------------------

The best way to interact with your hosts is to use the gce inventory plugin, which dynamically queries GCE and tells Ansible what nodes can be managed.

Note that when using the inventory script ``gce.py``, you also need to populate the ``gce.ini`` file that you can find in the contrib/inventory directory of the ansible checkout.

To use the GCE dynamic inventory script, copy ``gce.py`` from ``contrib/inventory`` into your inventory directory and make it executable. You can specify credentials for ``gce.py`` using the ``GCE_INI_PATH`` environment variable -- the default is to look for gce.ini in the same directory as the inventory script.

Let's see if inventory is working:

.. code-block:: bash

    $ ./gce.py --list

You should see output describing the hosts you have, if any, running in Google Compute Engine.

Now let's see if we can use the inventory script to talk to Google.

.. code-block:: bash

    $ GCE_INI_PATH=~/.gce.ini ansible all -i gce.py -m setup
    hostname | success >> {
      "ansible_facts": {
        "ansible_all_ipv4_addresses": [
          "x.x.x.x"
        ],

As with all dynamic inventory scripts in Ansible, you can configure the inventory path in ansible.cfg.  The recommended way to use the inventory is to create an ``inventory`` directory, and place both the ``gce.py`` script and a file containing ``localhost`` in it.  This can allow for cloud inventory to be used alongside local inventory (such as a physical datacenter) or machines running in different providers.

Executing ``ansible`` or ``ansible-playbook`` and specifying the ``inventory`` directory instead of an individual file will cause ansible to evaluate each file in that directory for inventory.

Let's once again use our inventory script to see if it can talk to Google Cloud:

.. code-block:: bash

    $ ansible all -i inventory/ -m setup
    hostname | success >> {
      "ansible_facts": {
        "ansible_all_ipv4_addresses": [
            "x.x.x.x"
        ],

The output should be similar to the previous command.  If you're wanting less output and just want to check for SSH connectivity, use "-m" ping instead.

Use Cases
---------

For the following use case, let's use this small shell script as a wrapper.

.. code-block:: bash

  #!/usr/bin/env bash
  PLAYBOOK="$1"

  if [[ -z $PLAYBOOK ]]; then
    echo "You need to pass a playbook as argument to this script."
    exit 1
  fi

  export SSL_CERT_FILE=$(pwd)/cacert.cer
  export ANSIBLE_HOST_KEY_CHECKING=False

  if [[ ! -f "$SSL_CERT_FILE" ]]; then
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
     connection: local

     vars:
       machine_type: n1-standard-1 # default
       image: debian-7
       service_account_email: unique-id@developer.gserviceaccount.com
       credentials_file: /path/to/project.json
       project_id: project-id

     tasks:
       - name: Launch instances
         gce:
             instance_names: dev
             machine_type: "{{ machine_type }}"
             image: "{{ image }}"
             service_account_email: "{{ service_account_email }}"
             credentials_file: "{{ credentials_file }}"
             project_id: "{{ project_id }}"
             tags: webserver
         register: gce

       - name: Wait for SSH to come up
         wait_for: host={{ item.public_ip }} port=22 delay=10 timeout=60
         with_items: "{{ gce.instance_data }}"

       - name: Add host to groupname
         add_host: hostname={{ item.public_ip }} groupname=new_instances
         with_items: "{{ gce.instance_data }}"

   - name: Manage new instances
     hosts: new_instances
     connection: ssh
     sudo: True
     roles:
       - base_configuration
       - production_server

Note that use of the "add_host" module above creates a temporary, in-memory group.  This means that a play in the same playbook can then manage machines
in the 'new_instances' group, if so desired.  Any sort of arbitrary configuration is possible at this point.

Configuring instances in a group
````````````````````````````````

All of the created instances in GCE are grouped by tag.  Since this is a cloud, it's probably best to ignore hostnames and just focus on group management.

Normally we'd also use roles here, but the following example is a simple one.  Here we will also use the "gce_net" module to open up access to port 80 on
these nodes.

The variables in the 'vars' section could also be kept in a 'vars_files' file or something encrypted with Ansible-vault, if you so choose.  This is just
a basic example of what is possible::

    - name: Setup web servers
      hosts: tag_webserver
      gather_facts: no

      vars:
        machine_type: n1-standard-1 # default
        image: debian-7
        service_account_email: unique-id@developer.gserviceaccount.com
        credentials_file: /path/to/project.json
        project_id: project-id

      roles:

        - name: Install lighttpd
          apt: pkg=lighttpd state=installed
          sudo: True

        - name: Allow HTTP
          local_action: gce_net
          args:
            fwname: "all-http"
            name: "default"
            allowed: "tcp:80"
            state: "present"
            service_account_email: "{{ service_account_email }}"
            credentials_file: "{{ credentials_file }}"
            project_id: "{{ project_id }}"

By pointing your browser to the IP of the server, you should see a page welcoming you.

Upgrades to this documentation are welcome, hit the github link at the top right of this page if you would like to make additions!
