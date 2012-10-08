.. _async_status:

async_status
``````````````````````````````

.. versionadded:: 0.5

This module gets the status of an asynchronous task. See: http://ansible.cc/docs/playbooks2.html#asynchronous-actions-and-polling 

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
    <td>jid</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>Job or task identifier</td>
    </tr>
        <tr>
    <td>mode</td>
    <td>no</td>
    <td>status</td>
    <td><ul><li>status</li><li>cleanup</li></ul></td>
    <td>if <code>status</code>, obtain the status; if <code>cleanup</code>, clean up the async job cache located in <code>~/.ansible_async/</code> for the specified job <em>jid</em>.</td>
    </tr>
        </table>

.. raw:: html

    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>See <a href='http://ansible.cc/docs/playbooks2.html#asynchronous-actions-and-polling'>http://ansible.cc/docs/playbooks2.html#asynchronous-actions-and-polling</a></p>
    