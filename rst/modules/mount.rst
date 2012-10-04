.. _mount:

mount
``````````````````````````````

.. versionadded:: 0.6

This module controls active and configured mount points in ``/etc/fstab``. 

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
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>device to be mounted on <em>name</em>.</td>
    </tr>
        <tr>
    <td>state</td>
    <td>yes</td>
    <td></td>
    <td><ul><li>present</li><li>absent</li><li>mounted</li><li>unmounted</li></ul></td>
    <td>If <code>mounted</code> or <code>unmounted</code>, the device will be actively mounted or unmounted as well as just configured in <em>fstab</em>. <code>absent</code> and <code>present</code> only deal with <em>fstab</em>.</td>
    </tr>
        <tr>
    <td>name</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>path to the mount point, eg: <code>/mnt/files</code></td>
    </tr>
        <tr>
    <td>dump</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>dump (see fstab(8))</td>
    </tr>
        <tr>
    <td>passno</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>passno (see fstab(8))</td>
    </tr>
        <tr>
    <td>opts</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>mount options (see fstab(8))</td>
    </tr>
        <tr>
    <td>fstype</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>file-system type</td>
    </tr>
        </table>

.. raw:: html

    <p>Mount DVD read-only</p>    <p><pre>
    mount name=/mnt/dvd src=/dev/sr0 fstype=iso9660 opts=ro
    </pre></p>
    <br/>

