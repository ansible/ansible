.. _vmware_rest_installation:

*****************************************
How to install the vmware_rest collection
*****************************************

.. contents::
  :local:
  

Requirements
============

The collection depends on:

- Ansible >=2.9.10 or greater
- Python 3.6 or greater

aiohttp
=======

aiohttp_ is the only dependency of the collection. You can install it with ``pip`` if you use a virtualenv to run Ansible.

.. code-block:: shell

    $ pip install aiohttp

Or using an RPM.

.. code-block:: shell

    $ sudo dnf install python3-aiohttp

.. _aiohttp: https://docs.aiohttp.org/en/stable/

Installation
============

The best option to install the collection is to use the ``ansible-galaxy`` command:

.. code-block:: shell


    $ ansible-galaxy collection install vmware.vmware_rest
