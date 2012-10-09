.. _group:

group
``````````````````````````````

.. versionadded:: 0.0.2

Manage presence of groups on a host. 

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
    <td>state</td>
    <td>no</td>
    <td>present</td>
    <td><ul><li>present</li><li>absent</li></ul></td>
    <td>Whether the group should be present or not on the remote host.</td>
    </tr>
        <tr>
    <td>gid</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Optional <em>GID</em> to set for the group.</td>
    </tr>
        <tr>
    <td>name</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>Name of the group to manage.</td>
    </tr>
        <tr>
    <td>system</td>
    <td>no</td>
    <td>no</td>
    <td><ul><li>True</li><li>False</li></ul></td>
    <td>If <em>yes</em>, indicates that the group created is a system group.</td>
    </tr>
        </table>

.. raw:: html

    <p>Example group command from Ansible Playbooks</p>    <p><pre>
    group name=somegroup state=present
    </pre></p>
    <br/>

