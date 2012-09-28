.. _lineinfile:

lineinfile
````````

.. versionadded:: 0.7


This module will search a file for a line, and ensure that it is present or absent. 
This is primarily useful when you want to change a single line in a file only. For other cases, see the ``copy`` or ``template`` modules. 


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
    <td>state</td>
    <td>False</td>
    <td>present</td>
    <td><ul><li>present</li><li>absent</li></ul></td>
    <td>Whether the line should be there or not.</td>
    </tr>
    
    <tr>
    <td>name</td>
    <td>True</td>
    <td></td>
    <td><ul></ul></td>
    <td>The file to modify</td>
    </tr>
    
    <tr>
    <td>insertafter</td>
    <td>False</td>
    <td>EOF</td>
    <td><ul><li>BOF</li><li>EOF</li></ul></td>
    <td>Used with <em>state=present</em>. If specified, the line will be inserted after the specified regular expression. Two special values are available; <code>BOF</code> for inserting the line at the beginning of the file, and <code>EOF</code> for inserting the line at the end of the file.</td>
    </tr>
    
    <tr>
    <td>regexp</td>
    <td>True</td>
    <td></td>
    <td><ul></ul></td>
    <td>The regular expression to look for in the file. For <em>state=present</em>, the pattern to replace. For <em>state=absent</em>, the pattern of the line to remove.</td>
    </tr>
    
    <tr>
    <td>line</td>
    <td>False</td>
    <td></td>
    <td><ul></ul></td>
    <td>Required for <em>state=present</em>. The line to insert/replace into the file. Must match the value given to <code>regexp</code>.</td>
    </tr>
    
    <tr>
    <td>backup</td>
    <td>False</td>
    <td>False</td>
    <td><ul></ul></td>
    <td>Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly.</td>
    </tr>
    
    </table>


.. raw:: html


    <p></p>
    <p><pre>
    lineinfile name=/etc/selinux/config regexp=^SELINUX= line=SELINUX=disabled</pre></p>

    <p></p>
    <p><pre>
    lineinfile name=/etc/sudoers state=absent regexp="^%wheel"</pre></p>

    <br/>

