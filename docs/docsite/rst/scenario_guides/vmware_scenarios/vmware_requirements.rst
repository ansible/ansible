.. _vmware_requirements:

********************
VMware Prerequisites
********************

.. contents::
   :local:

Installing SSL Certificates
===========================

All vCenter and ESXi servers require SSL encryption on all connections to enforce secure communication. You must enable SSL encryption for Ansible by installing the server's SSL certificates on your Ansible control node or delegate node.

If the SSL certificate of your vCenter or ESXi server is not correctly installed on your Ansible control node, you will see the following warning when using Ansible VMware modules:

``Unable to connect to vCenter or ESXi API at xx.xx.xx.xx on TCP/443: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:777)``

To install the SSL certificate for your VMware server,  and run your Ansible VMware modules in encrypted mode, please follow the instructions for the server you are running with VMware.

Installing vCenter SSL certificates for Ansible
-----------------------------------------------

* From any web browser, go to the base URL of the vCenter Server without port number like ``https://vcenter-domain.example.com``

* Click the "Download trusted root CA certificates" link at the bottom of the grey box on the right and download the file.

* Change the extension of the file to .zip. The file is a ZIP file of all root certificates and all CRLs.

* Extract the contents of the zip file. The extracted directory contains a ``.certs`` directory that contains two types of files. Files with a number as the extension (.0, .1, and so on) are root certificates.

* Install the certificate files are trusted certificates by the process that is appropriate for your operating system.


Installing ESXi SSL certificates for Ansible
--------------------------------------------

* Enable SSH Service on ESXi either by using Ansible VMware module `vmware_host_service_manager <https://github.com/ansible-collections/vmware/blob/main/plugins/modules/vmware_host_config_manager.py>`_ or manually using vSphere Web interface.

* SSH to ESXi server using administrative credentials, and navigate to directory ``/etc/vmware/ssl``

* Secure copy (SCP) ``rui.crt`` located in ``/etc/vmware/ssl`` directory to Ansible control node.

* Install the certificate file by the process that is appropriate for your operating system.

Using custom path for SSL certificates
--------------------------------------

If you need to use a custom path for SSL certificates, you can set the ``REQUESTS_CA_BUNDLE`` environment variable in your playbook.

For example, if ``/var/vmware/certs/vcenter1.crt`` is the SSL certificate for your vCenter Server, you can use the :ref:`environment <playbooks_environment>` keyword to pass it to the modules:

.. code-block:: yaml

   - name: Gather all tags from vCenter
     community.vmware.vmware_tag_info:
       validate_certs: True
       hostname: '{{ vcenter_hostname }}'
       username: '{{ vcenter_username }}'
       password: '{{ vcenter_password }}'
     environment:
       REQUESTS_CA_BUNDLE: /var/vmware/certs/vcenter1.crt

There is a `known issue <https://github.com/psf/requests/issues/3829>`_ in ``requests`` library (version 2) which you may want to consider when using this environment variable. Basically, setting ``REQUESTS_CA_BUNDLE`` environment variable on managed nodes overrides the ``validate_certs`` value. This may result in unexpected behavior while running the playbook. Please see `community.vmware issue 601 <https://github.com/ansible-collections/community.vmware/issues/601>`_ and `vmware issue 254 <https://github.com/vmware/vsphere-automation-sdk-python/issues/254>`_ for more information.
