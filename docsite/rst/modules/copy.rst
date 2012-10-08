.. _copy:

copy
``````````````````````````````


The ``copy`` module copies a file on the local box to remote locations. 

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
    <td>Remote absolute path where the file should be copied to.</td>
    </tr>
        <tr>
    <td>src</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>Local path to a file to copy to the remote server; can be absolute or relative.</td>
    </tr>
        <tr>
    <td>backup</td>
    <td>no</td>
    <td>no</td>
    <td><ul><li>yes</li><li>no</li></ul></td>
    <td>Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly. (added in Ansible 0.7)</td>
    </tr>
        <tr>
    <td>others</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>all arguments accepted by the <span class='module'>file</span> module also work here</td>
    </tr>
        </table>

.. raw:: html

    <p>Example from Ansible Playbooks</p>    <p><pre>
    copy src=/srv/myfiles/foo.conf dest=/etc/foo.conf owner=foo group=foo mode=0644
    </pre></p>
    <p>Copy a new <code>ntp.conf</code> file into place, backing up the original if it differs from the copied version</p>    <p><pre>
    copy src=/mine/ntp.conf dest=/etc/ntp.conf owner=root group=root mode=644 backup=yes
    </pre></p>
    <br/>

