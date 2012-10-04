.. _ini_file:

ini_file
``````````````````````````````

.. versionadded:: 0.9

Manage (add, remove, change) individual settings in an INI-style file without having to manage the file as a whole with, say, ``template`` or ``assemble``. Adds missing sections if they don't exist. 

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
    <td>option</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>if set (required for changing a <em>value</em>), this is the name of the option.May be omitted if adding/removing a whole <em>section</em>.</td>
    </tr>
        <tr>
    <td>others</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>all arguments accepted by the <span class='module'>file</span> module also work here</td>
    </tr>
        <tr>
    <td>dest</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>Path to the INI-style file; this file is created if required</td>
    </tr>
        <tr>
    <td>section</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>Section name in INI file. This is added if <code>state=present</code> automatically when a single value is being set.</td>
    </tr>
        <tr>
    <td>backup</td>
    <td>no</td>
    <td></td>
    <td><ul><li>yes</li><li>no</li></ul></td>
    <td>Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly.</td>
    </tr>
        <tr>
    <td>value</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>the string value to be associated with an <em>option</em>. May be omitted when removing an <em>option</em>.</td>
    </tr>
        </table>

.. raw:: html

    <p>Ensure <code>fav=lemonade</code> is in section <code>[drinks]</code> in said file</p>    <p><pre>
    ini_file dest=/etc/conf section=drinks option=fav value=lemonade mode=0600 backup=true
    </pre></p>
        <p><pre>
    ini_file dest=/etc/anotherconf
         section=drinks
         option=temperature
         value=cold
         backup=true

    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>While it is possible to add an <em>option</em> without specifying a <em>value</em>, this makes no sense.</p>
    