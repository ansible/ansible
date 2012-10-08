.. _setup:

setup
``````````````````````````````


This module is automatically called by playbooks to gather useful variables about remote hosts that can be used in playbooks. It can also be executed directly by ``/usr/bin/ansible`` to check what variables are available to a host. Ansible provides many *facts* about the system, automatically. 


.. raw:: html

    <p>Obtain facts from all hosts and store them indexed by hostname at /tmp/facts.</p>    <p><pre>
    ansible all -m setup -tree /tmp/facts
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>More ansible facts will be added with successive releases. If <em>facter</em> or <em>ohai</em> are installed, variables from these programs will also be snapshotted into the JSON file for usage in templating. These variables are prefixed with <code>facter_</code> and <code>ohai_</code> so it's easy to tell their source. All variables are bubbled up to the caller. Using the ansible facts and choosing to not install <em>facter</em> and <em>ohai</em> means you can avoid Ruby-dependencies on your remote systems.</p>
    