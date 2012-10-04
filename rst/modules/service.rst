.. _service:

service
``````````````````````````````

.. versionadded:: 0.1

Controls services on remote hosts. 

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
    <td>pattern</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>If the service does not respond to the status command, name a substring to look for as would be found in the output of the <em>ps</em> command as a stand-in for a status result.  If the string is found, the servie will be assumed to be running. (added in Ansible 0.7)</td>
    </tr>
        <tr>
    <td>state</td>
    <td>no</td>
    <td></td>
    <td><ul><li>running</li><li>started</li><li>stopped</li><li>restarted</li><li>reloaded</li></ul></td>
    <td><em>started</em>, <em>stopped</em>, <em>reloaded</em>, <em>restarted</em>. <em>Started</em>/<em>stopped</em> are idempotent actions that will not run commands unless necessary.  <em>restarted</em> will always bounce the service.  <em>reloaded</em> will always reload.</td>
    </tr>
        <tr>
    <td>enabled</td>
    <td>no</td>
    <td></td>
    <td><ul><li>yes</li><li>no</li></ul></td>
    <td>Whether the service should start on boot.</td>
    </tr>
        <tr>
    <td>name</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>Name of the service.</td>
    </tr>
        </table>

.. raw:: html

    <p>Example action from Ansible Playbooks</p>    <p><pre>
    service name=httpd state=started
    </pre></p>
    <p>Example action from Ansible Playbooks</p>    <p><pre>
    service name=httpd state=stopped
    </pre></p>
    <p>Example action from Ansible Playbooks</p>    <p><pre>
    service name=httpd state=restarted
    </pre></p>
    <p>Example action from Ansible Playbooks</p>    <p><pre>
    service name=httpd state=reloaded
    </pre></p>
    <p>Example action from Ansible Playbooks</p>    <p><pre>
    service name=foo pattern=/usr/bin/foo state=started
    </pre></p>
    <br/>

