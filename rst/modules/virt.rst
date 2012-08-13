.. _virt:

virt
````

Manages virtual machines supported by libvirt.  Requires that libvirt be installed
on the managed machine.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | yes      |         | name of the guest VM being managed                                         |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              |          |         | 'running', 'shutdown', 'destroyed', or 'undefined'.  Note that there may   |
|                    |          |         | be some lag for state requests like 'shutdown' since these refer only to   |
|                    |          |         | VM states.  After starting a guest, it may not be immediately accessible.  |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| command            |          |         | in addition to state management, various non-idempotent commands are       |
|                    |          |         | available.  See examples below.                                            |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    virt guest=alpha state=running
    virt guest=alpha state=shutdown
    virt guest=alpha state=destroyed
    virt guest=alpha state=undefined

Example guest management commands from /usr/bin/ansible::

    ansible host -m virt -a "guest=foo command=status"
    ansible host -m virt -a "guest=foo command=pause"
    ansible host -m virt -a "guest=foo command=unpause"
    ansible host -m virt -a "guest=foo command=get_xml"
    ansible host -m virt -a "guest=foo command=autostart"

Example host (hypervisor) management commands from /usr/bin/ansible::

    ansible host -m virt -a "command=freemem"
    ansible host -m virt -a "command=list_vms"
    ansible host -m virt -a "command=info"
    ansible host -m virt -a "command=nodeinfo"
    ansible host -m virt -a "command=virttype"
