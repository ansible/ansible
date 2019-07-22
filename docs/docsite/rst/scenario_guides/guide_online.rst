****************
Online.net Guide
****************

Introduction
============

Online is a French hosting company mainly known for providing bare-metal servers named Dedibox.
Check it out: `https://www.online.net/en <https://www.online.net/en>`_

Dynamic inventory for Online resources
--------------------------------------

Ansible has a dynamic inventory plugin that can list your resources.

1. Create a YAML configuration such as ``online_inventory.yml`` with this content:

.. code-block:: yaml

    plugin: online

2. Set your ``ONLINE_TOKEN`` environment variable with your token.
    You need to open an account and log into it before you can get a token.
    You can find your token at the following page: `https://console.online.net/en/api/access <https://console.online.net/en/api/access>`_

3. You can test that your inventory is working by running:

.. code-block:: bash

    $ ansible-inventory -v -i online_inventory.yml --list


4. Now you can run your playbook or any other module with this inventory:

.. code-block:: console

    $ ansible all -i online_inventory.yml -m ping
    sd-96735 | SUCCESS => {
        "changed": false,
        "ping": "pong"
    }
