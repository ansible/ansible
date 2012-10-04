.. _mysql_user:

mysql_user
``````````````````````````````

.. versionadded:: 0.6

Adds or removes a user from a MySQL database. 

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
    <td>name</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>name of the user (role) to add or remove</td>
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
    <td>host</td>
    <td>no</td>
    <td>localhost</td>
    <td><ul></ul></td>
    <td>the 'host' part of the MySQL username</td>
    </tr>
        <tr>
    <td>state</td>
    <td>no</td>
    <td>present</td>
    <td><ul><li>present</li><li>absent</li></ul></td>
    <td>The database state</td>
    </tr>
        <tr>
    <td>login_password</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>The password used to authenticate with</td>
    </tr>
        <tr>
    <td>password</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>set the user's password</td>
    </tr>
        <tr>
    <td>priv</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>MySQL privileges string in the format: <code>db.table:priv1,priv2</code></td>
    </tr>
        </table>

.. raw:: html

    <p>Create database user with name 'bob' and password '12345' with all database privileges</p>    <p><pre>
    mysql_user name=bob password=12345 priv=*.*:ALL state=present
    </pre></p>
    <p>Ensure no user named 'sally' exists, also passing in the auth credentials.</p>    <p><pre>
    mysql_user login_user=root login_password=123456 name=sally state=absent
    </pre></p>
    <p>Example privileges string format</p>    <p><pre>
    mydb.*:INSERT,UPDATE/anotherdb.*:SELECT/yetanotherdb.*:ALL
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>Requires the MySQLdb Python package on the remote host. For Ubuntu, this is as easy as apt-get install python-mysqldb.</p>
        <p>Both <code>login_password</code> and <code>login_username</code> are required when you are passing credentials. If none are present, the module will attempt to read the credentials from <code>~/.my.cnf</code>, and finally fall back to using the MySQL default login of 'root' with no password.</p>
    