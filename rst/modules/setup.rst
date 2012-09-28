.. _setup:

setup
````````



This module is automatically called by playbooks to gather useful variables about remote hosts that can be used in playbooks. It can also be executed directly by ``/usr/bin/ansible`` to check what variables are available to a host. Ansible provides many *facts* about the system, automatically. 




.. raw:: html


    <p>Obtain facts from all hosts and store them indexed by hostname at /tmp/facts.</p>
    <p><pre>
    ansible all -m setup -tree /tmp/facts</pre></p>

    <br/>

