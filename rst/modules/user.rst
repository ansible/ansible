.. _user:

user
``````````````````````````````

.. versionadded:: 0.2

Manage user accounts and user attributes. 

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
    <td>comment</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Optionally sets the description (aka <em>GECOS</em>) of user account.</td>
    </tr>
        <tr>
    <td>shell</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Optionally set the user's shell.</td>
    </tr>
        <tr>
    <td>force</td>
    <td>no</td>
    <td>no</td>
    <td><ul><li>True</li><li>False</li></ul></td>
    <td>When used with <em>state=absent</em>, behavior is as with <em>userdel --force</em>.</td>
    </tr>
        <tr>
    <td>name</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>Name of the user to create, remove or modify.</td>
    </tr>
        <tr>
    <td>createhome</td>
    <td>no</td>
    <td>yes</td>
    <td><ul><li>True</li><li>False</li></ul></td>
    <td>Unless set to <em>no</em>, a home directory will be made for the user when the account is created.</td>
    </tr>
        <tr>
    <td>system</td>
    <td>no</td>
    <td>no</td>
    <td><ul><li>True</li><li>False</li></ul></td>
    <td>When creating an account, setting this to <em>yes</em> makes the user a system account.  This setting cannot be changed on existing users.</td>
    </tr>
        <tr>
    <td>remove</td>
    <td>no</td>
    <td>no</td>
    <td><ul><li>True</li><li>False</li></ul></td>
    <td>When used with <em>state=absent</em>, behavior is as with <em>userdel --remove</em>.</td>
    </tr>
        <tr>
    <td>state</td>
    <td>no</td>
    <td>present</td>
    <td><ul><li>present</li><li>absent</li></ul></td>
    <td>Whether the account should exist.  When <em>absent</em>, removes the user account.</td>
    </tr>
        <tr>
    <td>groups</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Puts the user in this comma-delimited list of groups.</td>
    </tr>
        <tr>
    <td>home</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Optionally set the user's home directory.</td>
    </tr>
        <tr>
    <td>group</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Optionally sets the user's primary group (takes a group name).</td>
    </tr>
        <tr>
    <td>password</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Optionally set the user's password to this crypted value.  See the user example in the github examples directory for what this looks like in a playbook.</td>
    </tr>
        <tr>
    <td>append</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>If <em>yes</em>, will only add groups, not set them to just the list in <em>groups</em>.</td>
    </tr>
        <tr>
    <td>uid</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Optionally sets the <em>UID</em> of the user.</td>
    </tr>
        </table>

.. raw:: html

    <br/>

