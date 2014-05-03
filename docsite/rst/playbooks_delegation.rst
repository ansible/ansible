Delegation, Rolling Updates, and Local Actions
==============================================

.. contents:: Topics

Being designed for multi-tier deployments since the beginning, Ansible is great at doing things on one host on behalf of another, or doing local steps with reference to some remote hosts.

This in particular is very applicable when setting up continuous deployment infrastructure or zero downtime rolling updates, where you might be talking with load balancers or monitoring systems.

Additional features allow for tuning the orders in which things complete, and assigning a batch window size for how many machines to process at once during a rolling update.

This section covers all of these features.  For examples of these items in use, `please see the ansible-examples repository <http://github.com/ansible/ansible-examples/>`_. There are quite a few examples of zero-downtime update procedures for different kinds of applications.

You should also consult the :doc:`modules` section, various modules like 'ec2_elb', 'nagios', and 'bigip_pool', and 'netscaler' dovetail neatly with the concepts mentioned here.  

You'll also want to read up on :doc:`playbooks_roles`, as the 'pre_task' and 'post_task' concepts are the places where you would typically call these modules. 

.. _rolling_update_batch_size:

Rolling Update Batch Size
`````````````````````````

.. versionadded:: 0.7

By default, Ansible will try to manage all of the machines referenced in a play in parallel.  For a rolling updates
use case, you can define how many hosts Ansible should manage at a single time by using the ''serial'' keyword::


    - name: test play
      hosts: webservers
      serial: 3

In the above example, if we had 100 hosts, 3 hosts in the group 'webservers'
would complete the play completely before moving on to the next 3 hosts.

.. _maximum_failure_percentage:

Maximum Failure Percentage
``````````````````````````

.. versionadded:: 1.3

By default, Ansible will continue executing actions as long as there are hosts in the group that have not yet failed.
In some situations, such as with the rolling updates described above, it may be desirable to abort the play when a 
certain threshold of failures have been reached. To achieve this, as of version 1.3 you can set a maximum failure 
percentage on a play as follows::

    - hosts: webservers
      max_fail_percentage: 30
      serial: 10

In the above example, if more than 3 of the 10 servers in the group were to fail, the rest of the play would be aborted.

.. note::

     The percentage set must be exceeded, not equaled. For example, if serial were set to 4 and you wanted the task to abort 
     when 2 of the systems failed, the percentage should be set at 49 rather than 50.

.. _delegation:

Delegation
``````````

.. versionadded:: 0.7

This isn't actually rolling update specific but comes up frequently in those cases.

If you want to perform a task on one host with reference to other hosts, use the 'delegate_to' keyword on a task.
This is ideal for placing nodes in a load balanced pool, or removing them.  It is also very useful for controlling
outage windows.  Using this with the 'serial' keyword to control the number of hosts executing at one time is also
a good idea::

    ---

    - hosts: webservers
      serial: 5

      tasks:

      - name: take out of load balancer pool
        command: /usr/bin/take_out_of_pool {{ inventory_hostname }}
        delegate_to: 127.0.0.1

      - name: actual steps would go here
        yum: name=acme-web-stack state=latest

      - name: add back to load balancer pool
        command: /usr/bin/add_back_to_pool {{ inventory_hostname }}
        delegate_to: 127.0.0.1


These commands will run on 127.0.0.1, which is the machine running Ansible. There is also a shorthand syntax that you can use on a per-task basis: 'local_action'. Here is the same playbook as above, but using the shorthand syntax for delegating to 127.0.0.1::

    ---

    # ...

      tasks:

      - name: take out of load balancer pool
        local_action: command /usr/bin/take_out_of_pool {{ inventory_hostname }}

    # ...

      - name: add back to load balancer pool
        local_action: command /usr/bin/add_back_to_pool {{ inventory_hostname }}

A common pattern is to use a local action to call 'rsync' to recursively copy files to the managed servers.
Here is an example::

    ---
    # ...
      tasks:

      - name: recursively copy files from management server to target
        local_action: command rsync -a /path/to/files {{ inventory_hostname }}:/path/to/target/

Note that you must have passphrase-less SSH keys or an ssh-agent configured for this to work, otherwise rsync
will need to ask for a passphrase.

.. _local_playbooks:

Local Playbooks
```````````````

It may be useful to use a playbook locally, rather than by connecting over SSH.  This can be useful
for assuring the configuration of a system by putting a playbook on a crontab.  This may also be used
to run a playbook inside an OS installer, such as an Anaconda kickstart.

To run an entire playbook locally, just set the "hosts:" line to "hosts:127.0.0.1" and then run the playbook like so::

    ansible-playbook playbook.yml --connection=local

Alternatively, a local connection can be used in a single playbook play, even if other plays in the playbook
use the default remote connection type::

    - hosts: 127.0.0.1
      connection: local

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   `Ansible Examples on GitHub <http://github.com/ansible/ansible-examples>`_
       Many examples of full-stack deployments
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


