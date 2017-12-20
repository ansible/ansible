Vultr Cloud Guide
=================

.. _vultr_introduction:

Introduction
````````````
The purpose of this chaptter is to explain how to get started with Ansible in a Vultr context. You will find usage examples in the example section in of each module's doc.

The Vultr modules don't have any dependency other than Ansible itself.


Authentication
``````````````
The Vultr Ansible modules support a few different ways to authenticate to the Vultr API.

Module Argument api_key
~~~~~~~~~~~~~~~~~~~~~~~

The Ansible default way is to pass the key as an argument ``api_key`` within a task clause:

.. code-block:: yaml

    - name: ensure server exists
      local_action:
        module: vr_server
        name: "{{ vr_server_name }}"
        os: CentOS 7 x64
        plan: 1024 MB RAM,25 GB SSD,1.00 TB BW
        region: Amsterdam
        api_key: "{{ vultr_key }}"
        state: started

Credentials File
~~~~~~~~~~~~~~~~

If the ``apt_key`` argument was not passed, Ansible looks for a credentials file under the following locations (last one wins):

* A ``.vultr.ini`` (note the dot) file in the home directory.
* A ``VULTR_CONFIG`` environment variable pointing to an .ini file.
* A ``vultr.ini`` (without the dot) file in the current working directory, same directory as your playbooks are located.

Within the credentials file, the format has to be as the following:

.. code-block:: ini

    [default]
    key = GBDSS7CHXCQPPOAS21YH2HUKQSEQQ2TYPIGQ

The credentials file has multi key support, identified by a section name. The credentials file may or may not have a default section to be used as the default key.

.. code-block:: ini

    [default]
    key = UKQSEQQ2TYPIGWGBDSS7CHXCQPPOAS21YH2H

    [stage]
    key = POAS21YH2HUKQSEQQ2TYPIGQGBDSS7CHXCQP

    [production]
    key = PSFG84NX04GBDSSUDKJUKASLIEKJHC83MNNP

To select a section to be used, either pass the argument ``api_account`` within a task clause or alternatively set the env variable ``VULTR_API_ACCOUNT``

.. code-block:: yaml

    - name: ensure server exists
      local_action:
        module: vr_server
        name: "{{ vr_server_name }}"
        os: CentOS 7 x64
        plan: 1024 MB RAM,25 GB SSD,1.00 TB BW
        region: Amsterdam
        api_account: "{{ cloud_environment }}"
        state: started

Environment Variable Fallback
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If authentication is not handled, the Vultr module's fallback is to get the key from the environment variable ``VULTR_API_KEY``.

To change the default value of API arguments, like timeout or retries, a few more environment variable exists:

``VULTR_API_ACCOUNT``: For changing the default section in the vultr.ini file. Default: default

``VULTR_API_RETRIES``: Amount of retries in case of the Vultr API retuns an HTTP 503 code. Default: 10

``VULTR_API_TIMEOUT``: HTTP timeout in seconds to Vultr API. Default: 10
