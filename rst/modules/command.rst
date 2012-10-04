.. _command:

command
``````````````````````````````


The command module takes the command name followed by a list of space-delimited arguments. 
The given command will be executed on all selected nodes. It will not be processed through the shell, so variables like ``$HOME`` and operations like ``"<"``, ``">"``, ``"|"``, and ``"&"`` will not work. As such, all paths to commands must be fully qualified 

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
    <td>a filename, when it already exists, this step will <b>not</b> be run.</td>
    </tr>
        <tr>
    <td>free_form</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>the command module takes a free form command to run</td>
    </tr>
        <tr>
    <td>chdir</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>cd into this directory before running the command (added in Ansible 0.6)</td>
    </tr>
        <tr>
    <td>removes</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>a filename, when it does not exist, this step will <b>not</b> be run. (added in Ansible 0.8)</td>
    </tr>
        </table>

.. raw:: html

    <p>Example from Ansible Playbooks</p>    <p><pre>
    command /sbin/shutdown -t now
    </pre></p>
    <p><em>creates</em>, <em>removes</em>, and <em>chdir</em> can be specified after the command. For instance, if you only want to run a command if a certain file does not exist, use this.</p>    <p><pre>
    command /usr/bin/make_database.sh arg1 arg2 creates=/path/to/database
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>If you want to run a command through the shell (say you are using <code><</code>, <code>></code>, <code>|</code>, etc), you actually want the <span class='module'>shell</span> module instead. The <span class='module'>command</span> module is much more secure as it's not affected by the user's environment.</p>
    