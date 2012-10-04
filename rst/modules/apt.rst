.. _apt:

apt
``````````````````````````````

.. versionadded:: 0.0.2

Manages apt-packages (such as for Debian/Ubuntu). 

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
    <td>purge</td>
    <td>no</td>
    <td>no</td>
    <td><ul><li>yes</li><li>no</li></ul></td>
    <td>Will force purging of configuration files if the module state is set to <code>absent</code>.</td>
    </tr>
        <tr>
    <td>state</td>
    <td>no</td>
    <td>present</td>
    <td><ul><li>installed</li><li>latest</li><li>remove</li><li>absent</li><li>present</li></ul></td>
    <td>Indicates the desired package state</td>
    </tr>
        <tr>
    <td>force</td>
    <td>no</td>
    <td>no</td>
    <td><ul><li>yes</li><li>no</li></ul></td>
    <td>If <code>yes</code>, force installs/removes.</td>
    </tr>
        <tr>
    <td>pkg</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>A package name or package specifier with version, like <code>foo</code> or <code>foo=1.0</code></td>
    </tr>
        <tr>
    <td>update_cache</td>
    <td>no</td>
    <td>no</td>
    <td><ul><li>yes</li><li>no</li></ul></td>
    <td>Run the equivalent of <code>apt-get update</code> before the operation. Can be run as part of the package installation or as a seperate step</td>
    </tr>
        <tr>
    <td>default_release</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Corresponds to the <code>-t</code> option for <em>apt</em> and sets pin priorities</td>
    </tr>
        <tr>
    <td>install_recommends</td>
    <td>no</td>
    <td>no</td>
    <td><ul><li>yes</li><li>no</li></ul></td>
    <td>Corresponds to the <code>--no-install-recommends</code> option for <em>apt</em>, default behavior works as apt's default behavior, <code>no</code> does not install recommended packages. Suggested packages are never installed.</td>
    </tr>
        </table>

.. raw:: html

    <p>Update repositories cache and install <code>foo</code> package</p>    <p><pre>
    apt pkg=foo update-cache=yes
    </pre></p>
    <p>Remove <code>foo</code> package</p>    <p><pre>
    apt pkg=foo state=removed
    </pre></p>
    <p>Install the the package <code>foo</code></p>    <p><pre>
    apt pkg=foo state=installed
    </pre></p>
    <p>Install the version '1.00' of package <code>foo</code></p>    <p><pre>
    apt pkg=foo=1.00 state=installed
    </pre></p>
    <p>Update the repository cache and update package <code>ngnix</code> to latest version using default release <code>squeeze-backport</code></p>    <p><pre>
    apt pkg=nginx state=latest default-release=squeeze-backports update-cache=yes
    </pre></p>
    <p>Install latest version of <code>openjdk-6-jdk</code> ignoring <code>install-recomands</code></p>    <p><pre>
    apt pkg=openjdk-6-jdk state=latest install-recommends=no
    </pre></p>
    <br/>

