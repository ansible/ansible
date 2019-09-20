%define release_date %(date "+%a %b %e %Y")

# Disable shebang munging for specific paths.  These files are data files.
# ansible-test munges the shebangs itself.
%global __brp_mangle_shebangs_exclude_from /usr/lib/python[0-9]+\.[0-9]+/site-packages/ansible_test/_data/.*

# RHEL and Fedora add -s to the shebang line.  We do *not* use -s -E -S or -I
# with ansible because it has many optional features which users need to
# install libraries on their own to use.  For instance, paramiko for the
# network connection plugins or winrm to talk to windows hosts.
# Set this to nil to remove -s
%define py_shbang_opts %{nil}
%define py2_shbang_opts %{nil}
%define py3_shbang_opts %{nil}

%if 0%{?fedora} || 0%{?rhel} >= 8
%global with_python2 0
%global with_python3 1
%else
%global with_python2 1
%global with_python3 0
%endif

Name: ansible
Summary: SSH-based configuration management, deployment, and task execution system
Version: %{rpmversion}
Release: %{rpmrelease}%{?dist}%{?repotag}

Group: Development/Libraries
License: GPLv3+
Source0: https://releases.ansible.com/ansible/%{name}-%{upstream_version}.tar.gz

Url: http://ansible.com
BuildArch: noarch

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
%{!?python2_sitelib: %global python_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python3_sitelib: %global python_sitelib %(%{__python3} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

# Bundled provides
Provides: bundled(python-backports-ssl_match_hostname) = 3.7.0.1
Provides: bundled(python-distro) = 1.4.0
Provides: bundled(python-ipaddress) = 1.0.22
Provides: bundled(python-selectors2) = 1.1.1
Provides: bundled(python-six) = 1.12.0

%if 0%{?rhel} >= 8

# Bundled provides
Provides: bundled(python-backports-ssl_match_hostname) = 3.7.0.1
Provides: bundled(python-distro) = 1.4.0
Provides: bundled(python-ipaddress) = 1.0.22
Provides: bundled(python-selectors2) = 1.1.1
Provides: bundled(python-six) = 1.12.0

BuildRequires: python3-devel
BuildRequires: python3-setuptools

# man pages
BuildRequires: python3-docutils

# Tests
BuildRequires: python3-jinja2
BuildRequires: python3-PyYAML
BuildRequires: python3-cryptography
BuildRequires: python3-six

BuildRequires: python3-pytest
BuildRequires: python3-pytest-xdist
BuildRequires: python3-pytest-mock
BuildRequires: python3-requests
BuildRequires: python3-coverage
BuildRequires: python3-mock
BuildRequires: python3-boto3
BuildRequires: python3-botocore
BuildRequires: python3-systemd

BuildRequires: git-core

Requires: python3-jinja2

Requires: python3-PyYAML
Requires: python3-cryptography
Requires: python3-six
Requires: sshpass

%else

%if 0%{?rhel} >= 7
# RHEL 7
BuildRequires: python2-devel
BuildRequires: python-setuptools
# For building docs
BuildRequires: python-sphinx

# Tests
BuildRequires: python-jinja2
BuildRequires: PyYAML
BuildRequires: python2-cryptography
BuildRequires: python-six

# rhel7 does not have python-pytest but has pytest
BuildRequires: pytest
#BuildRequires: python-pytest-xdist
#BuildRequires: python-pytest-mock
BuildRequires: python-requests
BuildRequires: python-coverage
BuildRequires: python-mock
BuildRequires: python-boto3
#BuildRequires: python-botocore
BuildRequires: git

BuildRequires: python-paramiko
BuildRequires: python-jmespath
BuildRequires: python-passlib

Requires: python-jinja2

Requires: PyYAML
Requires: python2-cryptography
Requires: python-six
Requires: sshpass

Requires: python-passlib
Requires: python-paramiko
Requires: python2-jmespath

# The ansible-doc package is no longer provided as of Ansible Engine 2.6.0
Obsoletes: ansible-doc < 2.6.0
%endif  # Requires for RHEL 7
%endif  # Requires for RHEL 8


# FEDORA >= 29
%if 0%{?fedora} >= 29
BuildRequires: python3-devel
BuildRequires: python3-setuptools
Requires: python3-PyYAML
Requires: python3-paramiko
Requires: python3-jinja2
Requires: python3-httplib2
Requires: python3-setuptools
Requires: python3-six
Requires: sshpass
%endif

# SUSE/openSUSE
%if 0%{?suse_version}
BuildRequires: python-devel
BuildRequires: python-setuptools
Requires: python-paramiko
Requires: python-jinja2
Requires: python-yaml
Requires: python-httplib2
Requires: python-setuptools
Requires: python-six
Requires: sshpass
%endif


%description
Ansible is a radically simple model-driven configuration management,
multi-node deployment, and remote task execution system. Ansible works
over SSH and does not require any software or daemons to be installed
on remote nodes. Extension modules can be written in any language and
are transferred to managed machines automatically.

%package -n ansible-test
Summary: Tool for testing ansible plugin and module code
Requires: %{name} = %{version}-%{release}
%if 0%{?rhel} >= 8
# Will use the python3 stdlib venv
#Requires: python3-virtualenv
#BuildRequires: python3-virtualenv
%else
%if 0%{?rhel} >= 7
Requires: python-virtualenv
BuildRequires: python-virtualenv
%endif  # Requires for RHEL 7
%endif  # Requires for RHEL 8

# SUSE/openSUSE
%if 0%{?suse_version}
Requires: python-virtualenv
BuildRequires: python-virtualenv
%endif

%description -n ansible-test
Ansible is a radically simple model-driven configuration management,
multi-node deployment, and remote task execution system. Ansible works
over SSH and does not require any software or daemons to be installed
on remote nodes. Extension modules can be written in any language and
are transferred to managed machines automatically.
This package installs the ansible-test command for testing modules and plugins
developed for ansible.

%prep
%setup -q -n %{name}-%{upstream_version}

%build
%if %{with_python2}
%py2_build
%endif

%if %{with_python3}
%py3_build
%endif

%install
%if %{with_python2}
%{__python2} setup.py install --root=%{buildroot}
for i in %{buildroot}/%{_bindir}/{ansible,ansible-console,ansible-doc,ansible-galaxy,ansible-playbook,ansible-pull,ansible-vault}  ; do
    mv $i $i-%{python2_version}
    ln -s %{_bindir}/$(basename $i)-%{python2_version} $i
    ln -s %{_bindir}/$(basename $i)-%{python2_version} $i-2
done
%endif

%if %{with_python3}
%{__python3} setup.py install --root=%{buildroot}
%endif


# Amazon Linux doesn't install to dist-packages but python_sitelib expands to
# that location and the python interpreter expects things to be there.
if expr x'%{python_sitelib}' : 'x.*dist-packages/\?' ; then
    DEST_DIR='%{buildroot}%{python_sitelib}'
    SOURCE_DIR=$(echo "$DEST_DIR" | sed 's/dist-packages/site-packages/g')
    if test -d "$SOURCE_DIR" -a ! -d "$DEST_DIR" ; then
        mv $SOURCE_DIR $DEST_DIR
    fi
fi

# Create system directories that Ansible defines as default locations in
# ansible/config/base.yml
DATADIR_LOCATIONS='%{_datadir}/ansible/collections
%{_datadir}/ansible/plugins/doc_fragments
%{_datadir}/ansible/plugins/action
%{_datadir}/ansible/plugins/become
%{_datadir}/ansible/plugins/cache
%{_datadir}/ansible/plugins/callback
%{_datadir}/ansible/plugins/cliconf
%{_datadir}/ansible/plugins/connection
%{_datadir}/ansible/plugins/filter
%{_datadir}/ansible/plugins/httpapi
%{_datadir}/ansible/plugins/inventory
%{_datadir}/ansible/plugins/lookup
%{_datadir}/ansible/plugins/modules
%{_datadir}/ansible/plugins/module_utils
%{_datadir}/ansible/plugins/netconf
%{_datadir}/ansible/roles
%{_datadir}/ansible/plugins/strategy
%{_datadir}/ansible/plugins/terminal
%{_datadir}/ansible/plugins/test
%{_datadir}/ansible/plugins/vars'

UPSTREAM_DATADIR_LOCATIONS=$(grep -ri default lib/ansible/config/base.yml| tr ':' '\n' | grep '/usr/share/ansible')

if [ "$SYSTEM_LOCATIONS" != "$UPSTREAM_SYSTEM_LOCATIONS" ] ; then
	echo "The upstream Ansible datadir locations have changed.  Spec file needs to be updated"
	exit 1
fi

mkdir -p %{buildroot}%{_datadir}/ansible/plugins/
for location in $DATADIR_LOCATIONS ; do
	mkdir %{buildroot}"$location"
done
mkdir -p %{buildroot}%{_sysconfdir}/ansible/
mkdir -p %{buildroot}%{_sysconfdir}/ansible/roles/

cp examples/hosts %{buildroot}%{_sysconfdir}/ansible/
cp examples/ansible.cfg %{buildroot}%{_sysconfdir}/ansible/
mkdir -p %{buildroot}/%{_mandir}/man1/
cp -v docs/man/man1/*.1 %{buildroot}/%{_mandir}/man1/

cp -pr docs/docsite/rst .

%clean
rm -rf %{buildroot}

%check
# We need pytest-4.5.0 or greater
%if 0%{?fedora} >= 31
ln -s /usr/bin/pytest-3 bin/pytest
%{__python3} bin/ansible-test units -v --python %{python3_version}
%endif

%files
%defattr(-,root,root)
%{_bindir}/ansible*
%config(noreplace) %{_sysconfdir}/ansible/
%doc README.rst PKG-INFO COPYING changelogs/CHANGELOG*.rst
%doc %{_mandir}/man1/ansible*
%{_datadir}/ansible/
%if %{with_python3}
%{python3_sitelib}/ansible*
%exclude %{python3_sitelib}/ansible_test
%endif
%if %{with_python2}
%{python2_sitelib}/ansible*
%exclude %{python2_sitelib}/ansible_test
%endif

%files -n ansible-test
%{_bindir}/ansible-test
%if %{with_python3}
%{python3_sitelib}/ansible_test
%endif
%if %{with_python2}
%{python2_sitelib}/ansible_test
%endif

%changelog

* %{release_date} Ansible, Inc. <info@ansible.com> - %{rpmversion}-%{rpmrelease}
- Release %{rpmversion}-%{rpmrelease}
