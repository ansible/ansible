.. _fireball:

fireball
``````````````````````````````

.. versionadded:: 0.9

This modules launches an ephemeral *fireball* ZeroMQ message bus daemon on the remote node which Ansible can to communicate with nodes at high speed. 
The daemon listens on a configurable port for a configurable amount of time. 
Starting a new fireball as a given user terminates any existing user fireballs. 
Fireball mode is AES encrypted 

.. raw:: html

    <table>
    <tr>
    <th class="head">parameter</th>
    <th class="head">required</th>
    <th class="head">default</th>
    <th class="head">choices</th>
    <th class="head">comments</th>
    </tr>
        <tr>
    <td>minutes</td>
    <td>no</td>
    <td>30</td>
    <td><ul></ul></td>
    <td>The <em>fireball</em> listener daemon is started on nodes and will stay around for this number of minutes before turning itself off.</td>
    </tr>
        <tr>
    <td>port</td>
    <td>no</td>
    <td>5099</td>
    <td><ul></ul></td>
    <td>TCP port for ZeroMQ</td>
    </tr>
        </table>

.. raw:: html

    <p>This example playbook has two plays: the first launches <em>fireball</em> mode on all hosts via SSH, and the second actually starts using <em>fireball</em> node for subsequent management over the fireball interface</p>    <p><pre>
    - hosts: devservers
      gather_facts: false
      connection: ssh
      sudo: yes
      tasks:
          - action: fireball 

    - hosts: devservers
      connection: fireball
      tasks:
          - action: command /usr/bin/anything

    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>See the advanced playbooks chapter for more about using fireball mode.</p>
    