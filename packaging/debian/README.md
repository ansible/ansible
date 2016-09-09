Ansible Debian Package
======================

To create an Ansible DEB package:

    sudo apt-get install python-paramiko python-yaml python-jinja2 python-httplib2 python-setuptools python-six sshpass
    sudo apt-get install cdbs debhelper dpkg-dev git-core reprepro fakeroot asciidoc devscripts docbook-xml xsltproc libxml2-utils
    sudo apt-get install dh-python
    git clone git://github.com/ansible/ansible.git
    cd ansible
    make deb

On older releases that do not have `dh-python` (like Ubuntu 12.04), install `python-support` instead:

    sudo apt-get install python-support

The debian package file will be placed in the `../` directory. This can then be added to an APT repository or installed with `dpkg -i <package-file>`.

Note that `dpkg -i` does not resolve dependencies.

To install the Ansible DEB package and resolve dependencies:

    sudo dpkg -i <package-file>
    sudo apt-get -fy install

Or, if you are running Debian Stretch (or later) or Ubuntu Xenial (or later):

    sudo apt install <package-file>
