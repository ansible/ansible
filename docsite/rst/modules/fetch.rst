.. _fetch:

fetch
``````````````````````````````

.. versionadded:: 0.2

This module works like ``copy``, but in reverse. It is used for fetching files from remote machines and storing them locally in a file tree, organized by hostname. 

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
    <td>dest</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>A directory to save the file into. For example, if the <em>dest</em> directory is <code>/backup</code> a src file named <code>/etc/profile</code> on host <code>host.example.com</code>, would be saved into <code>/backup/host.example.com/etc/profile</code></td>
    </tr>
        <tr>
    <td>src</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>The file on the remote system to fetch. This must be a file, not a directory. Recursive fetching may be supported in a later release.</td>
    </tr>
        </table>

.. raw:: html

    <p>Example from Ansible Playbooks</p>    <p><pre>
    fetch src=/var/log/messages dest=/home/logtree
    </pre></p>
    <br/>

