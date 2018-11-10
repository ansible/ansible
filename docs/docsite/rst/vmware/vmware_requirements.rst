.. _vmware_requirements:

********************
VMware Prerequisites
********************

.. contents:: Topics


Installing SSL Certificate
==========================

All vCenter and ESXi servers require SSL encryption on all connections to enforce secure communication.

If you see the following warning while using Ansible VMware modules [warning], you need to enable SSL encryption for Ansible by installing the server's SSL certificates on your Ansible control node or delegate node.

```
Unable to connect to vCenter or ESXi API at xx.xx.xx.xx on TCP/443: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:777)
```

then, this means you need to add/install SSL certificate of vCenter or ESXi server in your Ansible control node.

The following instructions allow you to run your Ansible VMware modules with encrypted mode (viz. ``validate_certs=True``).

Please follow the instructions depending upon your server to install SSL certificate.

vCenter
-------

* From any web browser, go to the base URL of the vCenter Server without port number like ``https://vcenter-domain.example.com``

* Click the "Download trusted root CA certificates" link at the bottom of the grey box on the right and download the file.

* Change the extension of the file to .zip. The file is a ZIP file of all root certificates and all CRLs.

* Extract the contents of the zip file. The extracted directory contains a ``.certs`` directory that contains two types of files. Files with a number as the extension (.0, .1, and so on) are root certificates.

* Install the certificate files are trusted certificates by the process that is appropriate for your operating system.



ESXi
----

* Enable SSH Service on ESXi either by using Ansible VMware module `vmware_host_service_manager <https://github.com/ansible/ansible/blob/devel/lib/ansible/modules/cloud/vmware/vmware_host_config_manager.py>`_ or manually using vSphere Web interface.

* SSH to ESXi server using administrative credentials, and navigate to directory ``/etc/vmware/ssl``

* Secure copy (SCP) ``rui.crt`` located in ``/etc/vmware/ssl`` directory to Ansible control node.

* Install the certificate file by the process that is appropriate for your operating system.
