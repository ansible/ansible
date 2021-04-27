.. _k8s_ansible_inventory:

*****************************************
Using Kubernetes dynamic inventory plugin
*****************************************

.. contents::
  :local:

Kubernetes dynamic inventory plugin
===================================


The best way to interact with your Pods is to use the Kubernetes dynamic inventory plugin, which dynamically queries Kubernetes APIs using ``kubectl`` command line available on controller node and tells Ansible what Pods can be managed.

Requirements
------------

To use the Kubernetes dynamic inventory plugins, you must install `Kubernetes Python client <https://github.com/kubernetes-client/python>`_, `kubectl <https://github.com/kubernetes/kubectl>`_ and `OpenShift Python client <https://github.com/openshift/openshift-restclient-python>`_
on your control node (the host running Ansible).

.. code-block:: bash

    $ pip install kubernetes openshift

Please refer to Kubernetes official documentation for `installing kubectl <https://kubernetes.io/docs/tasks/tools/install-kubectl/>`_ on the given operating systems.

To use this Kubernetes dynamic inventory plugin, you need to enable it first by specifying the following in the ``ansible.cfg`` file:

.. code-block:: ini

  [inventory]
  enable_plugins = kubernetes.core.k8s

Then, create a file that ends in ``.k8s.yml`` or ``.k8s.yaml`` in your working directory.

The ``kubernetes.core.k8s`` inventory plugin takes in the same authentication information as any other Kubernetes modules.

Here's an example of a valid inventory file:

.. code-block:: yaml

    plugin: kubernetes.core.k8s

Executing ``ansible-inventory --list -i <filename>.k8s.yml`` will create a list of Pods that are ready to be configured using Ansible.

You can also provide the namespace to gather information about specific pods from the given namespace. For example, to gather information about Pods under the ``test`` namespace you will specify the ``namespaces`` parameter:

.. code-block:: yaml

    plugin: kubernetes.core.k8s
    connections:
    - namespaces:
        - test

Using vaulted configuration files
=================================

Since the inventory configuration file contains Kubernetes related sensitive information in plain text, a security risk, you may want to
encrypt your entire inventory configuration file.

You can encrypt a valid inventory configuration file as follows:

.. code-block:: bash

    $ ansible-vault encrypt <filename>.k8s.yml
      New Vault password:
      Confirm New Vault password:
      Encryption successful

    $ echo "MySuperSecretPassw0rd!" > /path/to/vault_password_file

And you can use this vaulted inventory configuration file using:

.. code-block:: bash

    $ ansible-inventory -i <filename>.k8s.yml --list --vault-password-file=/path/to/vault_password_file


.. seealso::

    `Kubernetes Python client <https://github.com/kubernetes-client/python>`_
        The GitHub Page of Kubernetes Python client
    `Kubernetes Python client - Issue Tracker <https://github.com/kubernetes-client/python/issues>`_
        The issue tracker for Kubernetes Python client
    `OpenShift Python client <https://github.com/openshift/openshift-restclient-python>`_
        The GitHub Page of OpenShift Dynamic API client
    `OpenShift Python client - Issue Tracker <https://github.com/openshift/openshift-restclient-python/issues>`_
        The issue tracker for OpenShift Dynamic API client
    `Kubectl installation <https://kubernetes.io/docs/tasks/tools/install-kubectl/>`_
        Installation guide for installing Kubectl
    :ref:`working_with_playbooks`
        An introduction to playbooks
    :ref:`playbooks_vault`
        Using Vault in playbooks
