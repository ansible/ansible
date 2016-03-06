Delegation, Rolling Updates, and Local Actions
==============================================

.. contents:: Topics

Being designed for multi-tier deployments since the beginning, Ansible is great at doing things on one host on behalf of another, or doing local steps with reference to some remote hosts.

This in particular is very applicable when setting up continuous deployment infrastructure or zero downtime rolling updates, where you might be talking with load balancers or monitoring systems.

Additional features allow for tuning the orders in which things complete, and assigning a batch window size for how many machines to process at once during a rolling update.

This section covers all of these features.  For examples of these items in use, `please see the ansible-examples repository <https://github.com/ansible/ansible-examples/>`_. There are quite a few examples of zero-downtime update procedures for different kinds of applications.

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

The ''serial'' keyword can also be specified as a percentage in Ansible 1.8 and later, which will be applied to the total number of hosts in a
play, in order to determine the number of hosts per pass::

    - name: test play
      hosts: websevers
      serial: "30%"

If the number of hosts does not divide equally into the number of passes, the final pass will contain the remainder.

.. note::
     No matter how small the percentage, the number of hosts per pass will always be 1 or greater.

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

.. _delegate_facts:

Delegated facts
```````````````

.. versionadded:: 2.0

By default, any fact gathered by a delegated task are assigned to the `inventory_hostname` (the current host) instead of the host which actually produced the facts (the delegated to host).
In 2.0, the directive `delegate_facts` may be set to `True` to assign the task's gathered facts to the delegated host instead of the current one.::


    - hosts: app_servers
      tasks:
        - name: gather facts from db servers
          setup:
          delegate_to: "{{item}}"
          delegate_facts: True
          with_items: "{{groups['dbservers']}}"

The above will gather facts for the machines in the dbservers group and assign the facts to those machines and not to app_servers.
This way you can lookup `hostvars['dbhost1']['default_ipv4_addresses'][0]` even though dbservers were not part of the play, or left out by using `--limit`.


.. _run_once:

Run Once
````````

.. versionadded:: 1.7

In some cases there may be a need to only run a task one time and only on one host. This can be achieved
by configuring "run_once" on a task::

    ---
    # ...

      tasks:

        # ...

        - command: /opt/application/upgrade_db.py
          run_once: true

        # ...

This can be optionally paired with "delegate_to" to specify an individual host to execute on::

        - command: /opt/application/upgrade_db.py
          run_once: true
          delegate_to: web01.example.org

When "run_once" is not used with "delegate_to" it will execute on the first host, as defined by inventory,
in the group(s) of hosts targeted by the play - e.g. webservers[0] if the play targeted "hosts: webservers".

This approach is similar to applying a conditional to a task such as::

        - command: /opt/application/upgrade_db.py
          when: inventory_hostname == webservers[0]

.. note::
     When used together with "serial", tasks marked as "run_once" will be ran on one host in *each* serial batch.
     If it's crucial that the task is run only once regardless of "serial" mode, use
     :code:`inventory_hostname == my_group_name[0]` construct.

.. _local_playbooks:

Local Playbooks
```````````````

It may be useful to use a playbook locally, rather than by connecting over SSH.  This can be useful
for assuring the configuration of a system by putting a playbook on a crontab.  This may also be used
to run a playbook inside an OS installer, such as an Anaconda kickstart.

To run an entire playbook locally, just set the "hosts:" line to "hosts: 127.0.0.1" and then run the playbook like so::

    ansible-playbook playbook.yml --connection=local

Alternatively, a local connection can be used in a single playbook play, even if other plays in the playbook
use the default remote connection type::

    - hosts: 127.0.0.1
      connection: local

.. _interrupt_execution_on_any_error:

Interrupt execution on any error
````````````````````````````````

With option ''any_errors_fatal'' any failure on any host in a multi-host play will be treated as fatal and Ansible will exit immediately without waiting for the other hosts.

Sometimes ''serial'' execution is unsuitable - number of hosts is unpredictable (because of dynamic inventory), speed is crucial (simultaneous execution is required). But all tasks must be 100% successful to continue playbook execution.

For example there is a service located in many datacenters, there a some load balancers to pass traffic from users to service. There is a deploy playbook to upgrade service deb-packages. Playbook stages:

- disable traffic on load balancers (must be turned off simultaneously)
- gracefully stop service
- upgrade software (this step includes tests and starting service)
- enable traffic on load balancers (should be turned off simultaneously)

Service can't be stopped with "alive" load balancers, they must be disabled, all of them. So second stage can't be played if any server failed on "stage 1".

For datacenter "A" playbook can be written this way::

    ---
    - hosts: load_balancers_dc_a
      any_errors_fatal: True
      tasks:
      - name: 'shutting down datacenter [ A ]'
        command: /usr/bin/disable-dc
    
    - hosts: frontends_dc_a
      tasks:
      - name: 'stopping service'
        command: /usr/bin/stop-software
      - name: 'updating software'
        command: /usr/bin/upgrade-software
    
    - hosts: load_balancers_dc_a
      tasks:
      - name: 'Starting datacenter [ A ]'
        command: /usr/bin/enable-dc


In this example Ansible will start software upgrade on frontends only if all load balancers are successfully disabled.

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   `Ansible Examples on GitHub <https://github.com/ansible/ansible-examples>`_
       Many examples of full-stack deployments
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


