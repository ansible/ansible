%define name ansible
%define release_date %(date "+%a %b %e %Y")

%if 0%{?rhel} == 5
%define __python2 /usr/bin/python26
%endif

Name:      %{name}
Version:   %{rpmversion}
Release:   %{rpmrelease}%{?dist}%{?repotag}
Url:       https://www.ansible.com
Summary:   SSH-based application deployment, configuration management, and IT orchestration platform
License:   GPLv3+
Group:     Development/Libraries
Source:    https://releases.ansible.com/ansible/%{name}-%{upstream_version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
%{!?__python2: %global __python2 /usr/bin/python2.6}
%{!?python_sitelib: %global python_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

BuildArch: noarch

# RHEL <=5
%if 0%{?rhel} && 0%{?rhel} <= 5
BuildRequires: python26-devel
BuildRequires: python26-setuptools
Requires: python26-PyYAML
Requires: python26-paramiko
Requires: python26-jinja2
Requires: python26-httplib2
Requires: python26-setuptools
Requires: python26-six
%endif

# RHEL == 6
%if 0%{?rhel} == 6
Requires: python-crypto
%endif

# RHEL >=7
%if 0%{?rhel} >= 7
Requires: python2-cryptography
%endif

# RHEL > 5
%if 0%{?rhel} && 0%{?rhel} > 5
BuildRequires: python2-devel
BuildRequires: python-setuptools
Requires: PyYAML
Requires: python-paramiko
Requires: python-jinja2
Requires: python-setuptools
Requires: python-six
%endif

# FEDORA > 17
%if 0%{?fedora} >= 18
BuildRequires: python-devel
BuildRequires: python-setuptools
Requires: PyYAML
Requires: python-paramiko
Requires: python-jinja2
Requires: python-httplib2
Requires: python-setuptools
Requires: python-six
%endif

# SuSE/openSuSE
%if 0%{?suse_version}
BuildRequires: python-devel
BuildRequires: python-setuptools
Requires: python-paramiko
Requires: python-jinja2
Requires: python-yaml
Requires: python-httplib2
Requires: python-setuptools
Requires: python-six
%endif

Requires: sshpass

%description

Ansible is a radically simple model-driven configuration management,
multi-node deployment, and orchestration engine. Ansible works
over SSH and does not require any software or daemons to be installed
on remote nodes. Extension modules can be written in any language and
are transferred to managed machines automatically.

%prep
%setup -q -n %{name}-%{upstream_version}

%build
%{__python2} setup.py build

%install
%{__python2} setup.py install --root=%{buildroot}

for i in %{buildroot}/%{_bindir}/{ansible,ansible-console,ansible-doc,ansible-galaxy,ansible-playbook,ansible-pull,ansible-vault}; do
    mv $i $i-%{python2_version}
    ln -s %{_bindir}/$(basename $i)-%{python2_version} $i
    ln -s %{_bindir}/$(basename $i)-%{python2_version} $i-2
done

# Amazon Linux doesn't install to dist-packages but python_sitelib expands to
# that location and the python interpreter expects things to be there.
if expr x'%{python_sitelib}' : 'x.*dist-packages/\?' ; then
    DEST_DIR='%{buildroot}%{python_sitelib}'
    SOURCE_DIR=$(echo "$DEST_DIR" | sed 's/dist-packages/site-packages/g')
    if test -d "$SOURCE_DIR" -a ! -d "$DEST_DIR" ; then
        mv $SOURCE_DIR $DEST_DIR
    fi
fi

mkdir -p %{buildroot}/etc/ansible/
mkdir -p %{buildroot}/etc/ansible/roles/
cp examples/hosts %{buildroot}/etc/ansible/
cp examples/ansible.cfg %{buildroot}/etc/ansible/
mkdir -p %{buildroot}/%{_mandir}/man1/
cp -v docs/man/man1/*.1 %{buildroot}/%{_mandir}/man1/
mkdir -p %{buildroot}/%{_datadir}/ansible

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%{python_sitelib}/ansible*
%{_bindir}/ansible*
%dir %{_datadir}/ansible
%config(noreplace) %{_sysconfdir}/ansible
%doc README.rst PKG-INFO COPYING changelogs/CHANGELOG*.rst
%doc %{_mandir}/man1/ansible*

%changelog

* %{release_date} Ansible, Inc. <info@ansible.com> - %{rpmversion}-%{rpmrelease}
- Release %{rpmversion}-%{rpmrelease}
