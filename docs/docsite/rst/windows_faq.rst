Windows Questions and Common Issues
===================================

Frequently Asked Questions
``````````````````````````
Here are some commonly asked questions in regards to Ansible and Windows and
their answers.

.. note:: These are questions around managing Windows servers with Ansible,
    questions about Ansible itself can be found at the faq_ page.

.. _faq: http://docs.ansible.com/ansible/latest/faq.html

TODO: add more questions and expand on answers

Does Ansible work with Windows XP and Server 2003
-------------------------------------------------
No

Can Ansible run on Windows?
---------------------------
No

Can I use SSH keys to Authenticate?
-----------------------------------
See certificate auth

I can run this command locally but it does not work under Ansible?
------------------------------------------------------------------
See WinRM limitations

This program won't install with Ansible
---------------------------------------
See above

What modules can I use?
-----------------------
Module list

Can I run Python modules?
-------------------------
No

Can I connect over SSH?
-----------------------
No


Common Issues
`````````````
Common issues that come up

Failed to connect to the host via ssh
-------------------------------------
Inventory is incorrect, set ``ansible_connection: winrm``

Trying to execute with /usr/bin/python
--------------------------------------
Inventory is incorrect, set ``ansible_connection: winrm``

Connection Refused
------------------
See windows_setup.rst

Credentials Rejected
--------------------
See windows_setup.rst

Access is Denied
----------------
WinRM restrictions

SSL CERTIFICATE_VERIFY_FAILED
-----------------------------
Ignore certificate validation or use 

credssp: 'module' object has no attribute 'TLSv1_2_METHOD'
----------------------------------------------------------
https://github.com/ansible/ansible/issues/23843

the connection attempt timed out
--------------------------------
Firewall or network connectivity, no listener
