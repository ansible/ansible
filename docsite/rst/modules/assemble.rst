.. _assemble:

assemble
``````````````````````````````

.. versionadded:: 0.5

Assembles a configuration file from fragments. Often a particular program will take a single configuration file and does not support a ``conf.d`` style structure where it is easy to build up the configuration from multiple sources. Assemble will take a directory of files that have already been transferred to the system, and concatenate them together to produce a destination file. Files are assembled in string sorting order. Puppet calls this idea *fragments*. 

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
    <td>dest</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>A file to create using the concatenation of all of the source files.</td>
    </tr>
        <tr>
    <td>src</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>An already existing directory full of source files.</td>
    </tr>
        <tr>
    <td>backup</td>
    <td>no</td>
    <td>no</td>
    <td><ul><li>yes</li><li>no</li></ul></td>
    <td>Create a backup file (if <code>yes</code>), including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly.</td>
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
    assemble src=/etc/someapp/fragments dest=/etc/someapp/someapp.conf
    </pre></p>
    <br/>

