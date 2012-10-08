.. _slurp:

slurp
``````````````````````````````


This module works like ``fetch``. It is used for fetching a base64- encoded blob containing the data in a remote file. 

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
    <td>src</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>The file on the remote system to fetch. This must be a file, not a directory.</td>
    </tr>
        </table>

.. raw:: html

    <p>Example using <code>/usr/bin/ansible</code></p>    <p><pre>
    ansible host -m slurp -a 'src=/tmp/xx'
    host | success >> {
       "content": "aGVsbG8gQW5zaWJsZSB3b3JsZAo=", 
       "encoding": "base64"
    }

    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>See also: <span class='module'>fetch</span></p>
    