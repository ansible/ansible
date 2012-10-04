.. _fail:

fail
``````````````````````````````

.. versionadded:: 0.8

This module fails the progress with a custom message. It can be useful for bailing out when a certain condition is met using only_if. 

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
    <td>msg</td>
    <td>no</td>
    <td>Failed because only_if condition is true</td>
    <td><ul></ul></td>
    <td>The customized message used for failing execution. If ommited, fail will simple bail out with a generic message.</td>
    </tr>
        <tr>
    <td>rc</td>
    <td>no</td>
    <td>1</td>
    <td><ul></ul></td>
    <td>The return code of the failure. This is currently not used by Ansible, but might be used in the future.</td>
    </tr>
        </table>

.. raw:: html

    <p>Example of how a playbook may fail when a condition is not met</p>    <p><pre>
    [{'action': 'fail msg="The system may not be provisioned according to the CMDB status."', 'only_if': "'$cmdb_status' != 'to-be-staged'"}]
    </pre></p>
    <br/>

