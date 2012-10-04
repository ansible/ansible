.. _shell:

shell
``````````````````````````````

.. versionadded:: 0.2

The shell module takes the command name followed by a list of arguments, space delimited. It is almost exactly like the ``command`` module but runs the command through the user's configured shell on the remote node. 

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
    <td>creates</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>a filename, when it already exists, this step will NOT be run</td>
    </tr>
        <tr>
    <td>chdir</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>cd into this directory before running the command (0.6 and later)</td>
    </tr>
        <tr>
    <td>(free form)</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>The command module takes a free form command to run</td>
    </tr>
        </table>

.. raw:: html

    <p>Execute the command in remote shell</p>    <p><pre>
    shell somescript.sh >> somelog.txt
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>If you want to execute a command securely and predicably, it may be better to use the <span class='module'>command</span> module instead. Best practices when writing playbooks will follow the trend of using <span class='module'>command</span> unless <span class='module'>shell</span> is explicitly required. When running ad-hoc commands, use your best judgement.</p>
    