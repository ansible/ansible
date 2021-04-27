.. _k8s_ansible_intro:

**************************************
Introduction to Ansible for Kubernetes
**************************************

.. contents::
  :local:

Introduction
============

Modules for interacting with the Kubernetes (K8s) and OpenShift API are under development, and can be used in preview mode. To use them, review the requirements, and then follow the installation and use instructions.

Requirements
============

To use the modules, you'll need the following:

- Run Ansible from source. For assistance, view :ref:`from_source`.
- `OpenShift Rest Client <https://github.com/openshift/openshift-restclient-python>`_ installed on the host that will execute the modules.


Installation
============

The Kubernetes modules are part of the `Ansible Kubernetes collection <https://github.com/ansible-collections/kubernetes.core>`_.

To install the collection, run the following:

.. code-block:: bash

    $ ansible-galaxy collection install kubernetes.core


Authenticating with the API
===========================

By default the OpenShift Rest Client will look for ``~/.kube/config``, and if found, connect using the active context. You can override the location of the file using the``kubeconfig`` parameter, and the context, using the ``context`` parameter.

Basic authentication is also supported using the ``username`` and ``password`` options. You can override the URL using the ``host`` parameter. Certificate authentication works through the ``ssl_ca_cert``, ``cert_file``, and ``key_file`` parameters, and for token authentication, use the ``api_key`` parameter.

To disable SSL certificate verification, set ``verify_ssl`` to false.

Reporting an issue
==================

If you find a bug or have a suggestion regarding modules, please file issues at `Ansible Kubernetes collection <https://github.com/ansible-collections/kubernetes.core>`_.
If you find a bug regarding OpenShift client, please file issues at `OpenShift REST Client issues <https://github.com/openshift/openshift-restclient-python/issues>`_.
If you find a bug regarding Kubectl binary, please file issues at `Kubectl issue tracker <https://github.com/kubernetes/kubectl>`_
