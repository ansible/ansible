.. _wait_for:

wait_for
``````````````````````````````

.. versionadded:: 0.7

This is useful for when services are not immediately available after their init scripts return - which is true of certain Java application servers. It is also useful when starting guests with the ``virt`` module and needing to pause until they are ready. 

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
    <td>delay</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>number of seconds to wait before starting to poll</td>
    </tr>
        <tr>
    <td>host</td>
    <td>no</td>
    <td>127.0.0.1</td>
    <td><ul></ul></td>
    <td>hostname or IP address to wait for</td>
    </tr>
        <tr>
    <td>port</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>port number to poll</td>
    </tr>
        <tr>
    <td>timeout</td>
    <td>no</td>
    <td>300</td>
    <td><ul></ul></td>
    <td>maximum number of seconds to wait for</td>
    </tr>
        <tr>
    <td>state</td>
    <td>no</td>
    <td>started</td>
    <td><ul><li>started</li><li>stopped</li></ul></td>
    <td>either <code>started</code>, or <code>stopped</code> depending on whether the module should poll for the port being open or closed.</td>
    </tr>
        </table>

.. raw:: html

    <p>Example from Ansible Playbooks</p>    <p><pre>
    wait_for port=8000 delay=10
    </pre></p>
    <br/>

