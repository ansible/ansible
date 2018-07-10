Ansible Debian Package
======================

To create an Ansible DEB package:

__Note__: You must run this target as root or set `PBUILDER_BIN='sudo pbuilder'`

```
apt-get install python-docutils cdbs debootstrap devscripts make pbuilder python-setuptools
git clone https://github.com/ansible/ansible.git
cd ansible
DEB_DIST='xenial trusty precise' make deb
```

Building in Docker:

```
git clone https://github.com/ansible/ansible.git
cd ansible
docker build -t ansible-deb-builder -f packaging/debian/Dockerfile .
docker run --privileged -e DEB_DIST='trusty' -v $(pwd):/ansible ansible-deb-builder
```

The debian package file will be placed in the `deb-build` directory. This can then be added to an APT repository or installed with `dpkg -i <package-file>`.

Note that `dpkg -i` does not resolve dependencies.

To install the Ansible DEB package and resolve dependencies:

```
dpkg -i <package-file>
apt-get -fy install
```

Or, if you are running Debian Stretch (or later) or Ubuntu Xenial (or later):

```
apt install /path/to/<package-file>
```
