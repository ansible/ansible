.. _file:

file
````````

.. versionadded:: 0.1


Sets attributes of files, symlinks, and directories, or removes files/symlinks/directories. Many other modules support the same options as the file module - including ``copy``, ``template``, and ``assmeble``. 


.. raw:: html

    <table>
    <tr>
    <td>parameter</td>
    <td>required</td>
    <td>default</td>
    <td>choices</td>
    <td>comments</td>
    </tr>
    
    <tr>
    <td>dest</td>
    <td>True</td>
    <td>[]</td>
    <td><ul></ul></td>
    <td>defines the file being managed, unless when used with <em>state=link</em>, and then sets the destination to create a symbolic link to using <em>src</em></td>
    </tr>
    
    <tr>
    <td>state</td>
    <td>False</td>
    <td>file</td>
    <td><ul><li>file</li><li>link</li><li>directory</li><li>absent</li></ul></td>
    <td>If directory, all immediate subdirectories will be created if they do not exist. If <em>file</em>, the file will NOT be created if it does not exist, see the <span class='module'>copy</span> or <span class='module'>template</span> module if you want that behavior. If <em>link</em>, the symbolic link will be created or changed. If absent, directories will be recursively deleted, and files or symlinks will be unlinked.</td>
    </tr>
    
    <tr>
    <td>mode</td>
    <td>False</td>
    <td></td>
    <td><ul></ul></td>
    <td>mode the file or directory should be, such as 0644 as would be fed to <em>chmod</em>. English modes like <b>g+x</b> are not yet supported</td>
    </tr>
    
    </table>


.. raw:: html


    <p>Example from Ansible Playbooks</p>
    <p><pre>
    file path=/etc/foo.conf owner=foo group=foo mode=0644</pre></p>

    <br/>

