.. _get_url:

get_url
``````````````````````````````

.. versionadded:: 0.6

Downloads files from HTTP, HTTPS, or FTP to the remote server. The remote server must have direct access to the remote resource. 

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
    <td>url</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>HTTP, HTTPS, or FTP URL</td>
    </tr>
        <tr>
    <td>dest</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>absolute path of where to download the file to.If <em>dest</em> is a directory, the basename of the file on the remote server will be used. If a directory, <em>thirsty=yes</em> must also be set.</td>
    </tr>
        <tr>
    <td>thirsty</td>
    <td>no</td>
    <td>no</td>
    <td><ul><li>yes</li><li>no</li></ul></td>
    <td>if <code>yes</code>, will download the file every time and replace the file if the contents change. if <code>no</code>, the file will only be downloaded if the destination does not exist. Generally should be <code>yes</code> only for small local files. prior to 0.6, acts if <code>yes</code> by default. (added in Ansible 0.7)</td>
    </tr>
        <tr>
    <td>others</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>all arguments accepted by the <span class='module'>file</span> module also work here</td>
    </tr>
        </table>

.. raw:: html

    <p>Example from Ansible Playbooks</p>    <p><pre>
    get_url url=http://example.com/path/file.conf dest=/etc/foo.conf mode=0440
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>This module doesn't yet support configuration for proxies or passwords.</p>
    