.. _easy_install:

easy_install
``````````````````````````````

.. versionadded:: 0.7

Installs Python libraries, optionally in a *virtualenv* 

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
    <td>virtualenv</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>an optional <em>virtualenv</em> directory path to install into. If the <em>virtualenv</em> does not exist, it is created automatically</td>
    </tr>
        <tr>
    <td>name</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>A Python library name</td>
    </tr>
        </table>

.. raw:: html

    <p>Examples from Ansible Playbooks</p>    <p><pre>
    easy_install name=pip
    </pre></p>
    <p>Install <em>Flask</em> (<a href='http://flask.pocoo.org/'>http://flask.pocoo.org/</a>) into the specified <em>virtualenv</em></p>    <p><pre>
    easy_install name=flask virtualenv=/webapps/myapp/venv
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>Please note that the <span class='module'>easy_install</span> module can only install Python libraries. Thus this module is not able to remove libraries. It is generally recommended to use the <span class='module'>pip</span> module which you can first install using <span class='module'>easy_install</span>.</p>
        <p>Also note that <em>virtualenv</em> must be installed on the remote host if the <code>virtualenv</code> parameter is specified.</p>
    