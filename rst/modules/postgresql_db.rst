.. _postgresql_db:

postgresql_db
``````````````````````````````

.. versionadded:: 0.6

Add or remove PostgreSQL databases from a remote host. 

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
    <td>login_password</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>The password used to authenticate with</td>
    </tr>
        <tr>
    <td>owner</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Name of the role to set as owner of the database</td>
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
        </table>

.. raw:: html

    <p>Create a new database with name 'acme'</p>    <p><pre>
    postgresql_db db=acme
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>The default authentication assumes that you are either logging in as or sudo'ing to the postgres account on the host.</p>
        <p>This module uses psycopg2, a Python PostgreSQL database adapter. You must ensure that psycopg2 is installed on the host before using this module. If the remote host is the PostgreSQL server (which is the default case), then PostgreSQL must also be installed on the remote host. For Ubuntu-based systems, install the postgresql, libpq-dev, and python-psycopg2 packages on the remote host before using this module.</p>
    