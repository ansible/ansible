.. _authorized_key:

authorized_key
``````````````````````````````

.. versionadded:: 0.5

Adds or removes an SSH authorized key for a user from a remote host. 

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
    <td>no</td>
    <td>present</td>
    <td><ul><li>present</li><li>absent</li></ul></td>
    <td>whether the given key should or should not be in the file</td>
    </tr>
        <tr>
    <td>user</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>Name of the user who should have access to the remote host</td>
    </tr>
        <tr>
    <td>key</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>the SSH public key, as a string</td>
    </tr>
        </table>

.. raw:: html

    <p>Example from Ansible Playbooks</p>    <p><pre>
    authorized_key user=charlie key="ssh-dss ASDF1234L+8BTwaRYr/rycsBF1D8e5pTxEsXHQs4iq+mZdyWqlW++L6pMiam1A8yweP+rKtgjK2httVS6GigVsuWWfOd7/sdWippefq74nppVUELHPKkaIOjJNN1zUHFoL/YMwAAAEBALnAsQN10TNGsRDe5arBsW8cTOjqLyYBcIqgPYTZW8zENErFxt7ij3fW3Jh/sCpnmy8rkS7FyK8ULX0PEy/2yDx8/5rXgMIICbRH/XaBy9Ud5bRBFVkEDu/r+rXP33wFPHjWjwvHAtfci1NRBAudQI/98DbcGQw5HmE89CjgZRo5ktkC5yu/8agEPocVjdHyZr7PaHfxZGUDGKtGRL2QzRYukCmWo1cZbMBHcI5FzImvTHS9/8B3SATjXMPgbfBuEeBwuBK5EjL+CtHY5bWs9kmYjmeo0KfUMH8hY4MAXDoKhQ7DhBPIrcjS5jPtoGxIREZjba67r6/P2XKXaCZH6Fc= charlie@example.org 2011-01-17"
    </pre></p>
    <p>Shorthand available in Ansible 0.8 and later</p>    <p><pre>
    authorized_key user=charlie key=$FILE(/home/charlie/.ssh/id_rsa.pub)
    </pre></p>
    <br/>

