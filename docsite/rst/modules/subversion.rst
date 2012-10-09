.. _subversion:

subversion
``````````````````````````````

.. versionadded:: 0.7

This module is really simple, so for now this checks out from the given branch of a repo at a particular SHA or tag. Latest is not supported, you should not be doing that. 

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
    <td>repo</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>The subversion URL to the repository.</td>
    </tr>
        <tr>
    <td>dest</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>Absolute path where the repository should be deployed.</td>
    </tr>
        <tr>
    <td>force</td>
    <td>no</td>
    <td>True</td>
    <td><ul><li>yes</li><li>no</li></ul></td>
    <td>If yes, any modified files in the working repository will be discarded. If no, this module will fail if it encounters modified files.</td>
    </tr>
        </table>

.. raw:: html

    <p>Export subversion repository in a specified folder</p>    <p><pre>
    subversion repo=svn+ssh://an.example.org/path/to/repo dest=/src/checkout
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>Requires subversion and grep on the client.</p>
    