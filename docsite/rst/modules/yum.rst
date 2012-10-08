.. _yum:

yum
``````````````````````````````


Will install, upgrade, remove, and list packages with the *yum* package manager. 

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
    <td><ul><li>present</li><li>latest</li><li>absent</li></ul></td>
    <td>whether to install (<code>present</code>, <code>latest</code>), or remove (<code>absent</code>) a package.</td>
    </tr>
        <tr>
    <td>list</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>various non-idempotent commands for usage with <code>/usr/bin/ansible</code> and <em>not</em> playbooks. See examples.</td>
    </tr>
        <tr>
    <td>name</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>package name, or package specifier with version, like <code>name-1.0</code>.</td>
    </tr>
        </table>

.. raw:: html

        <p><pre>
    yum name=httpd state=latest
    </pre></p>
        <p><pre>
    yum name=httpd state=removed
    </pre></p>
        <p><pre>
    yum name=httpd state=installed
    </pre></p>
    <br/>

