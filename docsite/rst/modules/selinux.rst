.. _selinux:

selinux
``````````````````````````````

.. versionadded:: 0.7

Configures the SELinux mode and policy. A reboot may be required after usage. Ansible will not issue this reboot but will let you know when it is required. 

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
    <td>policy</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>name of the SELinux policy to use (example: 'targeted')</td>
    </tr>
        <tr>
    <td>state</td>
    <td>yes</td>
    <td></td>
    <td><ul><li>enforcing</li><li>permissive</li><li>disabled</li></ul></td>
    <td>The SELinux mode</td>
    </tr>
        <tr>
    <td>conf</td>
    <td>no</td>
    <td>/etc/selinux/config</td>
    <td><ul></ul></td>
    <td>path to the SELinux configuration file, if non-standard</td>
    </tr>
        </table>

.. raw:: html

        <p><pre>
    selinux policy=targeted state=enforcing
    </pre></p>
        <p><pre>
    selinux policy=targeted state=disabled
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>Not tested on any debian based system</p>
    