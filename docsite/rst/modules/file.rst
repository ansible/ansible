.. _file:

file
``````````````````````````````


Sets attributes of files, symlinks, and directories, or removes files/symlinks/directories. Many other modules support the same options as the file module - including ``copy``, ``template``, and ``assmeble``. 

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
    <td>src</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>path of the file to link to (applies only to <code>state=link</code>).</td>
    </tr>
        <tr>
    <td>group</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>name of the group that should own the file/directory, as would be fed to <em>chown</em></td>
    </tr>
        <tr>
    <td>dest</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>defines the file being managed, unless when used with <em>state=link</em>, and then sets the destination to create a symbolic link to using <em>src</em></td>
    </tr>
        <tr>
    <td>selevel</td>
    <td>no</td>
    <td>s0</td>
    <td><ul></ul></td>
    <td>level part of the SELinux file context. This is the MLS/MCS attribute, sometimes known as the <code>range</code>. <code>_default</code> feature works as for <em>seuser</em>.</td>
    </tr>
        <tr>
    <td>seuser</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>user part of SELinux file context. Will default to system policy, if applicable. If set to <code>_default</code>, it will use the <code>user</code> portion of the the policy if available</td>
    </tr>
        <tr>
    <td>state</td>
    <td>no</td>
    <td>file</td>
    <td><ul><li>file</li><li>link</li><li>directory</li><li>absent</li></ul></td>
    <td>If <code>directory</code>, all immediate subdirectories will be created if they do not exist. If <code>file</code>, the file will NOT be created if it does not exist, see the <span class='module'>copy</span> or <span class='module'>template</span> module if you want that behavior. If <code>link</code>, the symbolic link will be created or changed. If <code>absent</code>, directories will be recursively deleted, and files or symlinks will be unlinked.</td>
    </tr>
        <tr>
    <td>serole</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>role part of SELinux file context, <code>_default</code> feature works as for <em>seuser</em>.</td>
    </tr>
        <tr>
    <td>mode</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>mode the file or directory should be, such as 0644 as would be fed to</td>
    </tr>
        <tr>
    <td>context</td>
    <td>no</td>
    <td></td>
    <td><ul><li>default</li></ul></td>
    <td>accepts only <code>default</code> as value. This will restore a file's SELinux context in the policy. Does nothing if no default value is available.</td>
    </tr>
        <tr>
    <td>owner</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>name of the user that should own the file/directory, as would be fed to <em>chown</em></td>
    </tr>
        <tr>
    <td>force</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>force is required when changing an existing file to a directory, or a link to a directory, and so on.  Use this with caution.</td>
    </tr>
        <tr>
    <td>setype</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>type part of SELinux file context, <code>_default</code> feature works as for <em>seuser</em>.</td>
    </tr>
        </table>

.. raw:: html

    <p>Example from Ansible Playbooks</p>    <p><pre>
    file path=/etc/foo.conf owner=foo group=foo mode=0644
    </pre></p>
        <p><pre>
    file src=/file/to/link/to dest=/path/to/symlink owner=foo group=foo state=link
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>See also <span class='module'>copy</span>, <span class='module'>template</span>, <span class='module'>assemble</span></p>
    