.. _apt_repository:

apt_repository
``````````````````````````````

.. versionadded:: 0.7

Manages apt repositores (such as for Debian/Ubuntu). 

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
    <td>The repository name/value</td>
    </tr>
        <tr>
    <td>state</td>
    <td>no</td>
    <td>present</td>
    <td><ul><li>present</li><li>absent</li></ul></td>
    <td>The repository state</td>
    </tr>
        </table>

.. raw:: html

    <p>Add nginx stable repository from PPA</p>    <p><pre>
    apt_repository repo=ppa://nginx/stable
    </pre></p>
    <p>Add specified repository into sources.</p>    <p><pre>
    apt_repository repo='deb http://archive.canonical.com/ubuntu hardy partner'
    </pre></p>
    <br/>

.. raw:: html

    <h4>Notes</h4>
        <p>This module works on Debian and Ubuntu only and requires <code>apt-add-repository</code> be available on destination server. To ensure this package is available use the <code>apt</code> module and install the <code>python-software-properties</code> package before using this module.</p>
        <p>A bug in <code>apt-add-repository</code> always adds <code>deb</code> and <code>deb-src</code> types for repositories (see the issue on Launchpad <a href='https://bugs.launchpad.net/ubuntu/+source/software-properties/+bug/987264'>https://bugs.launchpad.net/ubuntu/+source/software-properties/+bug/987264</a>), if a repo doesn't have source information (eg MongoDB repo from 10gen) the system will fail while updating repositories.</p>
    