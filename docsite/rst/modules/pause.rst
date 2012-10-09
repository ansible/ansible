.. _pause:

pause
``````````````````````````````

.. versionadded:: 0.8

Pauses playbook execution for a set amount of time, or until a prompt is acknowledged. All parameters are optional. The default behavior is to pause with a prompt. 
You can use ``ctrl+c`` if you wish to advance a pause earlier than it is set to expire or if you need to abort a playbook run entirely. To continue early: press ``ctrl+c`` and then ``c``. To abort a playbook: press ``ctrl+c`` and then ``a``. 
The pause module integrates into async/parallelized playbooks without any special considerations (see also: Rolling Updates). When using pauses with the ``serial`` playbook parameter (as in rolling updates) you are only prompted once for the current group of hosts. 

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
    <td>seconds</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Number of minutes to pause for.</td>
    </tr>
        <tr>
    <td>minutes</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Number of minutes to pause for.</td>
    </tr>
        <tr>
    <td>prompt</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Optional text to use for the prompt message.</td>
    </tr>
        </table>

.. raw:: html

    <p>Pause for 5 minutes to build app cache.</p>    <p><pre>
    pause minutes=5
    </pre></p>
    <p>Pause until you can verify updates to an application were successful.</p>    <p><pre>
    pause
    </pre></p>
    <p>A helpful reminder of what to look out for post-update.</p>    <p><pre>
    pause prompt=Make sure org.foo.FooOverload exception is not present
    </pre></p>
    <br/>

