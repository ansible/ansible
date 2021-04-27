.. _k8s_object_template:

*******************
Creating K8S object
*******************

.. contents::
  :local:

Introduction
============

This guide will show you how to utilize Ansible to create Kubernetes objects such as Pods, Deployments, and Secrets.

Scenario Requirements
=====================

* Software

    * Ansible 2.9.10 or later must be installed

    * The Python modules ``openshift`` and ``kubernetes`` must be installed on the Ansible controller (or Target host if not executing against localhost)

    * Kubernetes Cluster

    * Kubectl binary installed on the Ansible controller


* Access / Credentials

    * Kubeconfig configured with the given Kubernetes cluster


Assumptions
===========

- User has required level of authorization to create, delete and update resources on the given Kubernetes cluster.

Caveats
=======

- community.kubernetes 1.1.0 is going to migrate to `kubernetes.core <https://github.com/ansible-collections/kubernetes.core>`_

Example Description
===================

In this use case / example, we will create a Pod in the given Kubernetes Cluster.  The following Ansible playbook showcases the basic parameters that are needed for this.

.. literalinclude:: task_outputs/Add_a_pod_using_k8s.yaml

Since Ansible utilizes the Kubernetes API to perform actions, in this use case we will be connecting directly to the Kubernetes cluster.

To begin, there are a few bits of information we will need. Here you are using Kubeconfig which is pre-configured in your machine. The Kubeconfig is generally located at ``~/.kube/config``. It is highly recommended to store sensitive information such as password, user certificates in a more secure fashion using :ref:`ansible-vault` or using `Ansible Tower credentials <https://docs.ansible.com/ansible-tower/latest/html/userguide/credentials.html>`_.

Now you need to supply the information about the Pod which will be created. Using ``definition`` parameter of the ``kubernetes.core.k8s`` module, you specify `PodTemplate <https://kubernetes.io/docs/concepts/workloads/pods/#pod-templates>`_. This PodTemplate is identical to what you provide to the ``kubectl`` command.

What to expect
--------------

- You will see a bit of JSON output after this playbook completes. This output shows various parameters that are returned from the module and from cluster about the newly created Pod.

.. literalinclude:: task_outputs/Add_a_pod_using_k8s.json

- In the above example, 'changed' is ``True`` which notifies that the Pod creation started on the given cluster. This can take some time depending on your environment.


Troubleshooting
---------------

Things to inspect

- Check if the values provided for username and password are correct
- Check if the Kubeconfig is populated with correct values

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
