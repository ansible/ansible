Getting started with Cisco ACI
==============================

.. contents:: Topics

.. _aci_intro:

What is Cisco ACI ?
-------------------

Application Centric Infrastructure (ACI)
........................................
The Cisco Application Centric Infrastructure (ACI) allows application requirements to define the network. This architecture simplifies, optimizes, and accelerates the entire application deployment life cycle.

Application Policy Infrastructure Controller (APIC)
...................................................
The Cisco Application Policy Infrastructure Controller (APIC) API enables applications to directly connect with a secure, shared, high-performance resource pool that includes network, compute, and storage capabilities.

The APIC manages the scalable ACI multi-tenant fabric. The APIC provides a unified point of automation and management, policy programming, application deployment, and health monitoring for the fabric. The APIC, which is implemented as a replicated synchronized clustered controller, optimizes performance, supports any application anywhere, and provides unified operation of the physical and virtual infrastructure.

The APIC enables network administrators to easily define the optimal network for applications. Data center operators can clearly see how applications consume network resources, easily isolate and troubleshoot application and infrastructure problems, and monitor and profile resource usage patterns.

ACI Fabric
..........
The Cisco Application Centric Infrastructure (ACI) Fabric includes Cisco Nexus 9000 Series switches with the APIC to run in the leaf/spine ACI fabric mode. These switches form a "fat-tree" network by connecting each leaf node to each spine node; all other devices connect to the leaf nodes. The APIC manages the ACI fabric.

The ACI fabric provides consistent low-latency forwarding across high-bandwidth links (40 Gbps, with a 100-Gbps future capability). Traffic with the source and destination on the same leaf switch is handled locally, and all other traffic travels from the ingress leaf to the egress leaf through a spine switch. Although this architecture appears as two hops from a physical perspective, it is actually a single Layer 3 hop because the fabric operates as a single Layer 3 switch.

The ACI fabric object-oriented operating system (OS) runs on each Cisco Nexus 9000 Series node. It enables programming of objects for each configurable element of the system. The ACI fabric OS renders policies from the APIC into a concrete model that runs in the physical infrastructure. The concrete model is analogous to compiled software; it is the form of the model that the switch operating system can execute.

All the switch nodes contain a complete copy of the concrete model. When an administrator creates a policy in the APIC that represents a configuration, the APIC updates the logical model. The APIC then performs the intermediate step of creating a fully elaborated policy that it pushes into all the switch nodes where the concrete model is updated.

The APIC is responsible for fabric activation, switch firmware management, network policy configuration, and instantiation. While the APIC acts as the centralized policy and network management engine for the fabric, it is completely removed from the data path, including the forwarding topology. Therefore, the fabric can still forward traffic even when communication with the APIC is lost.

More information
................
Various resources exist to start learning ACI, here is a list of interesting articles from the community.

- `Adam Raffe: Learning ACI <https://adamraffe.com/learning-aci/>`_
- `Luca Relandini: ACI for dummies <http://lucarelandini.blogspot.be/2015/03/aci-for-dummies.html>`_
- `Jacob McGill: Automating Cisco ACI with Ansible <https://blogs.cisco.com/developer/automating-cisco-aci-with-ansible-eliminates-repetitive-day-to-day-tasks>`_


Using the ACI modules
---------------------
The Ansible ACI modules provide a user-friendly interface to managing your ACI environment using Ansible playbooks.

For instance ensuring that a specific tenant exists, is done using the following Ansible task:

.. code-block:: yaml

    - name: Ensure tenant customer-xyz exists
      aci_tenant:
        host: my-apic-1
        username: admin
        password: my-password
    
        tenant: customer-xyz
        description: Customer XYZ
        state: present

A complete list of existing ACI modules is available for `the latest stable release <http://docs.ansible.com/ansible/latest/list_of_network_modules.html#aci>`_ as well as `the current development version <http://docs.ansible.com/ansible/devel/module_docs/list_of_network_modules.html#aci>`_.

Standard module parameters
..........................
Every Ansible ACI module accepts the following parameters that influence the module's communication with the APIC REST API:

- ``host`` -- Hostname or IP address of the APIC
- ``port`` -- Port to use for communication *(defaults to `443` for HTTPS, and `80` for HTTP)*
- ``username`` -- User name used to log on to the APIC *(defaults to `admin`)*
- ``password`` -- Password for ``username`` to log on to the APIC (using password-based authentication)
- ``private_key`` -- Private key for ``username`` to log on to APIC (using signature-based authentication)
- ``certificate_name`` -- Name of the certificate in the ACI Web GUI *(defaults to `private_key` file baseename)*
- ``validate_certs`` -- Validate certificate when using HTTPS communication *(defaults to `yes`)*
- ``use_ssl`` -- Use HTTPS or HTTP for APIC REST communication *(defaults to `yes`)*
- ``use_proxy`` -- Use system proxy settings *(defaults to `yes`)*
- ``timeout`` -- Timeout value for socket-level communication


.. _aci_auth:

ACI authentication
------------------

Password-based authentication
.............................
If you want to logon using a username and password, you can use the following parameters with your ACI modules:

.. code-block:: yaml

    username: admin
    password: my-password

Password-based authentication is very simple to work with, but it is not the most efficient form of authentication from ACI's point-of-view as it requires a separate login-request and an open session to work. To avoid having your session time-out and requiring another login, you can use the more efficient Signature-based authentication.

.. note:: Password-based authentication also may trigger anti-DoS measures in ACI v3.1+ that causes session throttling and results in HTTP 503 errors and login failures.

.. warning:: Never store passwords in plain text.

The "Vault" feature of Ansible allows you to keep sensitive data such as passwords or keys in encrypted files, rather than as plain text in your playbooks or roles. These vault files can then be distributed or placed in source control. See :doc:`playbooks_vault` for more information.



Signature-based authentication using certificates
.................................................
Using signature-based authentication is more efficient and more reliable than password-based authentication.

Generate certificate and private key
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
Signature-based authentication requires a (self-signed) X.509 certificate with private key, and a configuration step for your AAA user in ACI. To generate a working X.509 certificate and private key, use the following procedure:

.. code-block:: bash

    $ openssl req -new -newkey rsa:1024 -days 36500 -nodes -x509 -keyout admin.key -out admin.crt -subj '/CN=Admin/O=Your Company/C=US'

Configure your local user
,,,,,,,,,,,,,,,,,,,,,,,,,
Perform the following steps:

- Add the X.509 certificate to your ACI AAA local user at **ADMIN > AAA**
- Click **AAA Authentication**
- Check that in the **Authentication** field the **Realm** field displays **Local**
- Expand **Security Management > Local Users**
- Click the name of the user you want to add a certificate to, in the **User Certificates** area
- Click the **+** sign and in the **Create X509 Certificate** enter a certificate name in the **Name** field
- If you use the basename of your private key here, you don't need to enter **certificate_name** in Ansible)
- Copy and paste your X.509 certificate in the **Data** field.

You can automate this by using the following Ansible task:

.. code-block:: yaml

    - name: Ensure we have a certificate installed
      aci_aaa_user_certificate:
        host: my-apic-1
        username: admin
        password: my-password
    
        aaa_user: admin
        certificate_name: admin
        certificate: "{{ lookup('file', 'pki/admin.crt') }}"  # This wil read the certificate data from a local file

.. note:: Signature-based authentication only works with local users.


Use Signature-based Authentication with Ansible
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
You need the following parameters with your ACI module(s) for it to work:

.. code-block:: yaml

    username: admin
    private_key: pki/admin.key
    certificate_name: admin  # This could be left out !

.. note:: If you use a certificate name in ACI that matches the private key's basename, you can leave out the ``certificate_name`` parameter like the example above.

More information
,,,,,,,,,,,,,,,,
More information about Signature-based Authentication is available from `Cisco APIC Signature-Based Transactions <https://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/kb/b_KB_Signature_Based_Transactions.html>`_.


.. _aci_rest:

Using ACI REST with Ansible
---------------------------
While already a lot of ACI modules exists in the Ansible distribution, and the most common actions can be performed with these existing modules, there's always something that may not be possible with off-the-shelf modules.

The :ref:`aci_rest <aci_rest>` module provides you with direct access to the APIC REST API and enables you to perform any task not already covered by the existing modules. This may seem like a complex undertaking, but you can generate the needed REST payload for any action performed in the ACI web interface effortless.

Using the aci-rest module
.........................
The :ref:`aci_rest <aci_rest>` module accepts the native XML and JSON payloads, but additionally accepts inline YAML payload (structured like JSON). The XML payload requires you to use a path ending with ``.xml`` whereas JSON or YAML require path to end with ``.json``.

When you're making modifications, you can use the POST or DELETE methods, whereas doing just queries require the GET method.

For instance, if you would like to ensure a specific tenant exists on ACI, these below four examples are identical:

**XML** (Native ACI)

.. code-block:: yaml

    - aci_rest:
        host: my-apic-1
        private_key: pki/admin.key
    
        method: post
        path: /api/mo/uni.xml
        content: |
          <fvTenant name="customer-xyz" descr="Customer XYZ"/>

**JSON** (Native ACI)

.. code-block:: yaml

    - aci_rest:
        host: my-apic-1
        private_key: pki/admin.key
    
        method: post
        path: /api/mo/uni.json
        content:
          {
            "fvTenant": {
              "attributes": {
                "name": "customer-xyz",
                "descr": "Customer XYZ"
              }
            }
          }

**YAML** (Ansible-style)

.. code-block:: yaml

    - aci_rest:
        host: my-apic-1
        private_key: pki/admin.key
    
        method: post
        path: /api/mo/uni.json
        content:
          fvTenant:
            attributes:
              name: customer-xyz
              descr: Customer XYZ

**Ansible task** (Dedicated module)

.. code-block:: yaml

    - aci_tenant:
        host: my-apic-1
        private_key: pki/admin.key
    
        tenant: customer-xyz
        description: Customer XYZ
        state: present

More information
................
- `APIC REST API Configuration Guide <https://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/2-x/rest_cfg/2_1_x/b_Cisco_APIC_REST_API_Configuration_Guide.html>`_



.. _aci_issues:

Known issues
............
The :ref:`aci_rest <aci_rest>` module is a wrapper around the APIC REST API. As a result any issues related to the APIC will be reflected in the use of the :ref:`aci_rest <aci_rest>` module.


Specific requests may not reflects changes correctly
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
There is a known issue where specific requests to the APIC do not properly reflect changed in the resulting output, even when we request those changes explicitly from the APIC. In one instance using the path ``api/node/mo/uni/infra.xml`` fails, where ``api/node/mo/uni/infra/.xml`` does work correctly.

This issue has been reported to the vendor.

**NOTE:** Fortunately the behaviour is consistent, so if you have a working example you can trust that it will keep on working.

More information from: `#35401 aci_rest: change not detected <https://github.com/ansible/ansible/issues/35041>`_


Specific requests are known to not be idempotent
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
The behaviour of the APIC is inconsistent to the use of ``status="created"`` and ``status="deleted"``. The result is that when you use ``status="created"`` in your payload the resulting tasks are not idempotent and creation will fail when the object was already created. However this is not the case with ``status="deleted"`` where such call to an non-existing object does not cause any failure whatsoever.

This issue has been reported to the vendor.

.. note:: A workaround is to avoid using ``status="created"`` and instead use ``status="modified"`` when idempotency is essential to your workflow..

More information from: `#35050 aci_rest: Using status="created" behaves differently than status="deleted" <https://github.com/ansible/ansible/issues/35050>`_


.. _aci_ops:

Operational examples
--------------------
Here is a small overview of useful operational tasks to reuse in your playbooks.
Feel free to contribute more snippets that are useful for others.

Waiting for all controllers to be ready
.......................................
You can use the below task after you started to build your APICs and configured the cluster to wait until all the APICs have come online. It will wait until the number of controllers equals the number listed in the ``apic`` inventory group.

.. code-block:: yaml

    - name: Waiting for all controllers to be ready
      aci_rest:
        host: '{{ apic_ip }}'
        username: '{{ apic_username }}'
        private_key: pki/admin.key
        method: get
        path: /api/node/class/topSystem.json?query-target-filter=eq(topSystem.role,"controller")
      changed_when: no
      register: aci_ready
      until: aci_ready|success and aci_ready.totalCount|int >= groups['apic']|count
      retries: 20
      delay: 30

Waiting for cluster to be fully-fit
...................................
The below example waits until the cluster is fully-fit. In this example you know the number of APICs in the cluster and you verify each APIC reports a 'fully-fit' status.

.. code-block:: yaml

    - name: Waiting for cluster to be fully-fit
      aci_rest:
        host: '{{ apic_ip }}'
        username: '{{ apic_username }}'
        private_key: pki/admin.key
        method: get
        path: /api/node/class/infraWiNode.json?query-target-filter=wcard(infraWiNode.dn,"topology/pod-1/node-1/av")
      changed_when: no
      register: aci_fit
      until: >
        aci_fit|success and
        aci_fit.totalCount|int >= groups['apic']|count >= 3 and
        aci_fit.imdata[0].infraWiNode.attributes.health == 'fully-fit' and
        aci_fit.imdata[1].infraWiNode.attributes.health == 'fully-fit' and
        aci_fit.imdata[2].infraWiNode.attributes.health == 'fully-fit'
    #    all(apic.infraWiNode.attributes.health == 'fully-fit' for apic in aci_fit.imdata)
      retries: 30
      delay: 30
