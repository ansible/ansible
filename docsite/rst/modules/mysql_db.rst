.. _mysql_db:

mysql_db
``````````````````````````````

.. versionadded:: 0.6

Add or remove MySQL databases from a remote host. 

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
    <td>The database state</td>
    </tr>
        <tr>
    <td>name</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>name of the database to add or remove</td>
    </tr>
        <tr>
    <td>encoding</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Encoding mode</td>
    </tr>
        <tr>
    <td>collation</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Collation mode</td>
    </tr>
        <tr>
    <td>login_user</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>The username used to authenticate with</td>
    </tr>
        <tr>
    <td>login_host</td>
    <td>no</td>
    <td>localhost</td>
    <td><ul></ul></td>
    <td>Host running the database</td>
    </tr>
        <tr>
    <td>login_password</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>The password used to authenticate with</td>
    </tr>
        </table>

.. raw:: html

    <p>Create a new database with name 'bobdata'</p>    <p><pre>
    mysql_db db=bobdata state=present
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>Requires the MySQLdb Python package on the remote host. For Ubuntu, this is as easy as apt-get install python-mysqldb.</p>
        <p>Both <code>login_password</code> and <code>login_username</code> are required when you are passing credentials. If none are present, the module will attempt to read the credentials from <code>~/.my.cnf</code>, and finally fall back to using the MySQL default login of 'root' with no password.</p>
    