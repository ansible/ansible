.. _template:

template
``````````````````````````````


Templates are processed by the Jinja2 templating language (http://jinja.pocoo.org/docs/) - documentation on the template formatting can be found in the Template Designer Documentation (http://jinja.pocoo.org/docs/templates/). 

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
    <td>Location to render the template to on the remote machine.</td>
    </tr>
        <tr>
    <td>src</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>Path of a Jinja2 formatted template on the local server. This can be a relative or absolute path.</td>
    </tr>
        <tr>
    <td>backup</td>
    <td>no</td>
    <td>no</td>
    <td><ul><li>yes</li><li>no</li></ul></td>
    <td>Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly.</td>
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
    template src=/mytemplates/foo.j2 dest=/etc/file.conf owner=bin group=wheel mode=0644
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>Since Ansible version 0.9, templates are loaded with <code>trim_blocks=True</code>.</p>
    