.. _supervisorctl:

supervisorctl
``````````````````````````````

.. versionadded:: 0.7

Manage the state of a program or group of programs running via Supervisord 

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
    <td><ul><li>started</li><li>stopped</li><li>restarted</li></ul></td>
    <td>The state of service</td>
    </tr>
        <tr>
    <td>name</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>The name of the supervisord program/process to manage</td>
    </tr>
        </table>

.. raw:: html

    <p>Manage the state of program <em>my_app</em> to be in <em>started</em> state.</p>    <p><pre>
    supervisorctl name=my_app state=started
    </pre></p>
    <br/>

