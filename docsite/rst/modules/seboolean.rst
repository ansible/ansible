.. _seboolean:

seboolean
``````````````````````````````

.. versionadded:: 0.7

Toggles SELinux booleans. 

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
    <td>yes</td>
    <td></td>
    <td><ul><li>true</li><li>false</li></ul></td>
    <td>Desired boolean value</td>
    </tr>
        <tr>
    <td>name</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>Name of the boolean to configure</td>
    </tr>
        <tr>
    <td>persistent</td>
    <td>no</td>
    <td></td>
    <td><ul><li>yes</li><li>no</li></ul></td>
    <td>Set to 'yes' if the boolean setting should survive a reboot</td>
    </tr>
        </table>

.. raw:: html

    <p>Set <em>httpd_can_network_connect</em> SELinux flag to <em>true</em> and <em>persistent</em></p>    <p><pre>
    seboolean name=httpd_can_network_connect state=true persistent=yes
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>Not tested on any debian based system</p>
    