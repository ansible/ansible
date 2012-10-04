.. _virt:

virt
``````````````````````````````

.. versionadded:: 0.2

Manages virtual machines supported by *libvirt*. 

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
    <td>no</td>
    <td><ul><li>running</li><li>shutdown</li><li>destroyed</li><li>undefined</li></ul></td>
    <td>Note that there may be some lag for state requests like <code>shutdown</code> since these refer only to VM states. After starting a guest, it may not be immediately accessible.</td>
    </tr>
        <tr>
    <td>command</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>in addition to state management, various non-idempotent commands are available. See examples</td>
    </tr>
        <tr>
    <td>name</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>name of the guest VM being managed</td>
    </tr>
        </table>

.. raw:: html

    <p>Example from Ansible Playbooks</p>    <p><pre>
    virt guest=alpha state=running
    </pre></p>
    <p>Example guest management with <code>/usr/bin/ansible</code></p>    <p><pre>
    ansible host -m virt -a "guest=alpha command=status"
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>Other non-idempotent commands are: <code>status</code>, <code>pause</code>, <code>unpause</code>, <code>get_xml</code>, <code>autostart</code>, <code>freemem</code>, <code>list_vms</code>, <code>info</code>, <code>nodeinfo</code>, <code>virttype</code></p>
    