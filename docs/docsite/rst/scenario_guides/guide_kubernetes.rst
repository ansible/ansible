Kubernetes and OpenShift Guide
==============================

Modules for interacting with the Kubernetes (K8s) and OpenShift API are under development, and can be used in preview mode. To use them, review the requirements, and then follow the installation and use instructions.

Requirements
------------

To use the modules, you'll need the following:

- Run Ansible from source. For assistance, view :ref:`from_source`.
- `OpenShift Rest Client <https://github.com/openshift/openshift-restclient-python>`_ installed on the host that will execute the modules.


Installation and use
--------------------

The Kubernetes modules are part of the `Ansible Kubernetes collection <https://github.com/ansible-collections/community.kubernetes>`_.

To install the collection, run the following:

.. code-block:: bash

    $ ansible-galaxy collection install community.kubernetes

Next, include it in a playbook, as follows:

.. code-block:: bash

    ---
    - hosts: localhost
      tasks:
      - name: Create a pod
        community.kubernetes.k8s:
          state: present
          definition:
            apiVersion: v1
            kind: Pod
            metadata:
              name: "utilitypod-1"
              namespace: default
              labels:
                app: galaxy
            spec:
              containers:
              - name: utilitypod
                image: busybox


Authenticating with the API
---------------------------

By default the OpenShift Rest Client will look for ``~/.kube/config``, and if found, connect using the active context. You can override the location of the file using the``kubeconfig`` parameter, and the context, using the ``context`` parameter.

Basic authentication is also supported using the ``username`` and ``password`` options. You can override the URL using the ``host`` parameter. Certificate authentication works through the ``ssl_ca_cert``, ``cert_file``, and ``key_file`` parameters, and for token authentication, use the ``api_key`` parameter.

To disable SSL certificate verification, set ``verify_ssl`` to false.

Filing issues
`````````````

If you find a bug or have a suggestion regarding modules, please file issues at `Ansible Kubernetes collection <https://github.com/ansible-collections/community.kubernetes>`_.
If you find a bug regarding OpenShift client, please file issues at `OpenShift REST Client issues <https://github.com/openshift/openshift-restclient-python/issues>`_.
