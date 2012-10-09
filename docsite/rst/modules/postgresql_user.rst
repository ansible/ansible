.. _postgresql_user:

postgresql_user
``````````````````````````````

.. versionadded:: 0.6

Add or remove PostgreSQL users (roles) from a remote host and, optionally, grant the users access to an existing database or tables. 
The fundamental function of the module is to create, or delete, roles from a PostgreSQL cluster. Privilege assignment, or removal, is an optional step, which works on one database at a time. This allows for the module to be called several times in the same module to modify the permissions on different databases, or to grant permissions to already existing users. 
A user cannot be removed untill all the privileges have been stripped from the user. In such situation, if the module tries to remove the user it will fail. To avoid this from happening the fail_on_user option signals the module to try to remove the user, but if not possible keep going; the module will report if changes happened and separately if the user was removed or not. 

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
    <td>postgres</td>
    <td><ul></ul></td>
    <td>User (role) used to authenticate with PostgreSQL</td>
    </tr>
        <tr>
    <td>login_host</td>
    <td>no</td>
    <td>localhost</td>
    <td><ul></ul></td>
    <td>Host running PostgreSQL.</td>
    </tr>
        <tr>
    <td>db</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>name of database where permissions will be granted</td>
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
    <td>Password used to authenticate with PostgreSQL</td>
    </tr>
        <tr>
    <td>password</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>set the user's password</td>
    </tr>
        <tr>
    <td>fail_on_user</td>
    <td>no</td>
    <td>True</td>
    <td><ul><li>yes</li><li>no</li></ul></td>
    <td>if yes, fail when user can't be removed. Otherwise just log and continue</td>
    </tr>
        <tr>
    <td>priv</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>PostgreSQL privileges string in the format: <code>table:priv1,priv2</code></td>
    </tr>
        </table>

.. raw:: html

    <p>Create django user and grant access to database and products table</p>    <p><pre>
    postgresql_user db=acme user=django password=ceec4eif7ya priv=CONNECT/products:ALL
    </pre></p>
    <p>Remove test user privileges from acme</p>    <p><pre>
    postgresql_user db=acme user=test priv=ALL/products:ALL state=absent fail_on_user=no
    </pre></p>
    <p>Remove test user from test database and the cluster</p>    <p><pre>
    postgresql_user db=test user=test priv=ALL state=absent
    </pre></p>
    <p>Example privileges string format</p>    <p><pre>
    INSERT,UPDATE/table:SELECT/anothertable:ALL
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>The default authentication assumes that you are either logging in as or sudo'ing to the postgres account on the host.</p>
        <p>This module uses psycopg2, a Python PostgreSQL database adapter. You must ensure that psycopg2 is installed on the host before using this module. If the remote host is the PostgreSQL server (which is the default case), then PostgreSQL must also be installed on the remote host. For Ubuntu-based systems, install the postgresql, libpq-dev, and python-psycopg2 packages on the remote host before using this module.</p>
    