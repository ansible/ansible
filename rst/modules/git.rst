.. _git:

git
``````````````````````````````

.. versionadded:: 0.0.1

Manage git checkouts of repositories to deploy files or software. 

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
    <td>repo</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>git, ssh, or http protocol address of the git repository.</td>
    </tr>
        <tr>
    <td>dest</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>Absolute path of where the repository should be checked out to.</td>
    </tr>
        <tr>
    <td>version</td>
    <td>no</td>
    <td>HEAD</td>
    <td><ul></ul></td>
    <td>What version of the repository to check out.  This can be the git <em>SHA</em>, the literal string <em>HEAD</em>, branch name, or a tag name.</td>
    </tr>
        <tr>
    <td>force</td>
    <td>no</td>
    <td>yes</td>
    <td><ul><li>True</li><li>False</li></ul></td>
    <td>(New in 0.7)  If yes, any modified files in the working repository will be discarded.  Prior to 0.7, this was always 'yes' and could not be disabled.</td>
    </tr>
        <tr>
    <td>remote</td>
    <td>no</td>
    <td>origin</td>
    <td><ul></ul></td>
    <td>Name of the remote branch.</td>
    </tr>
        </table>

.. raw:: html

    <p>Example git checkout from Ansible Playbooks</p>    <p><pre>
    git repo=git://foosball.example.org/path/to/repo.git dest=/srv/checkout version=release-0.22
    </pre></p>
    <br/>

