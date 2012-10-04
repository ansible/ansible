.. _pip:

pip
``````````````````````````````

.. versionadded:: 0.7

Manage Python library dependencies. 

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
    <td>An optional path to a virtualenv directory to install into</td>
    </tr>
        <tr>
    <td>state</td>
    <td>no</td>
    <td>present</td>
    <td><ul><li>present</li><li>absent</li><li>latest</li></ul></td>
    <td>The state of module</td>
    </tr>
        <tr>
    <td>version</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>The version number to install of the Python library specified in the 'name' parameter</td>
    </tr>
        <tr>
    <td>requirements</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>The path to a pip requirements file</td>
    </tr>
        <tr>
    <td>name</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>The name of a Python library to install</td>
    </tr>
        </table>

.. raw:: html

    <p>Install <em>flask</em> python package.</p>    <p><pre>
    pip name=flask
    </pre></p>
    <p>Install <em>flask</em> python package on version 0.8.</p>    <p><pre>
    pip name=flask version=0.8
    </pre></p>
    <p>Install <em>Flask</em> (<a href='http://flask.pocoo.org/'>http://flask.pocoo.org/</a>) into the specified <em>virtualenv</em></p>    <p><pre>
    pip name=flask virtualenv=/srv/webapps/my_app/venv
    </pre></p>
    <p>Install specified python requirements.</p>    <p><pre>
    pip requirements=/srv/webapps/my_app/src/requirements.txt
    </pre></p>
    <p>Install specified python requirements in indicated virtualenv.</p>    <p><pre>
    pip requirements=/srv/webapps/my_app/src/requirements.txt virtualenv=/srv/webapps/my_app/venv
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>Please note that <a href='http://www.virtualenv.org/, virtualenv'>http://www.virtualenv.org/, virtualenv</a> must be installed on the remote host if the virtualenv parameter is specified.</p>
    