%if 0%{?rhel} && 0%{?rhel} <= 5
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
%endif

Name: ansible
Release: 1%{?dist}
Summary: SSH-based configuration management, deployment, and orchestration engine
Version: 1.2.1

Group: Development/Libraries
License: GPLv3
Source0: http://ansible.cc/releases/%{name}-%{version}.tar.gz
Url: http://ansible.cc

BuildArch: noarch
%if 0%{?rhel} && 0%{?rhel} <= 5
BuildRequires: python26-devel

Requires: python26-PyYAML
Requires: python26-paramiko
Requires: python26-jinja2
%else
BuildRequires: python2-devel

Requires: PyYAML
Requires: python-paramiko
Requires: python-jinja2
%endif

%description

Ansible is a radically simple model-driven configuration management,
multi-node deployment, and orchestration engine. Ansible works
over SSH and does not require any software or daemons to be installed
on remote nodes. Extension modules can be written in any language and
are transferred to managed machines automatically.

%package fireball
Summary: Ansible fireball transport support
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}
%if 0%{?rhel} && 0%{?rhel} <= 5
Requires: python26-keyczar
Requires: python26-zmq
%else
Requires: python-keyczar
Requires: python-zmq
%endif

%description fireball

Ansible can optionally use a 0MQ based transport mechanism, which is
considerably faster than the standard ssh mechanism when there are
multiple actions, but requires additional supporting packages.

%package node-fireball
Summary: Ansible fireball transport - node end support
Group: Development/Libraries
%if 0%{?rhel} && 0%{?rhel} <= 5
Requires: python26-keyczar
Requires: python26-zmq
%else
Requires: python-keyczar
Requires: python-zmq
%endif

%description node-fireball

Ansible can optionally use a 0MQ based transport mechanism, which has
additional requirements for nodes to use.  This package includes those
requirements.

%prep
%setup -q

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --root=$RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/etc/ansible/
cp examples/hosts $RPM_BUILD_ROOT/etc/ansible/
cp examples/ansible.cfg $RPM_BUILD_ROOT/etc/ansible/
mkdir -p $RPM_BUILD_ROOT/%{_mandir}/{man1,man3}/
cp -v docs/man/man1/*.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
cp -v docs/man/man3/*.3 $RPM_BUILD_ROOT/%{_mandir}/man3/
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/ansible
cp -rv library/* $RPM_BUILD_ROOT/%{_datadir}/ansible/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{python_sitelib}/ansible*
%{_bindir}/ansible*
%dir %{_datadir}/ansible
%{_datadir}/ansible/*/*
#%{_datadir}/ansible/*/f[a-hj-z]*
#%{_datadir}/ansible/*/file
%config(noreplace) %{_sysconfdir}/ansible
%doc README.md PKG-INFO COPYING
%doc %{_mandir}/man1/ansible*
%doc %{_mandir}/man3/ansible.*
#%doc %{_mandir}/man3/ansible.f[a-hj-z]*
#%doc %{_mandir}/man3/ansible.file*
%doc examples/playbooks

%files fireball
%{_datadir}/ansible/utilities/fireball
%doc %{_mandir}/man3/ansible.fireball.*

%files node-fireball
%doc README.md PKG-INFO COPYING

%changelog

* Thu Jul 04 2013 Michael DeHaan <michael.dehaan@gmail.com> - 1.2-1
* Release 1.2.1

* Mon Jun 10 2013 Michael DeHaan <michael.dehaan@gmail.com> - 1.2-0
* Release 1.2

* Tue Apr 2 2013 Michael DeHaan <michael.dehaan@gmail.com> - 1.1-0
* Release 1.1

* Fri Feb 1 2013 Michael DeHaan <michael.dehaan@gmail.com> - 1.0-0
- Release 1.0

* Fri Nov 30 2012 Michael DeHaan <michael.dehaan@gmail.com> - 0.9-0
- Release 0.9

* Fri Oct 19 2012 Michael DeHaan <michael.dehaan@gmail.com> - 0.8-0
- Release of 0.8

* Thu Aug 6 2012 Michael DeHaan <michael.dehaan@gmail.com> - 0.7-0
- Release of 0.7

* Mon Aug 6 2012 Michael DeHaan <michael.dehaan@gmail.com> - 0.6-0
- Release of 0.6

* Wed Jul 4 2012 Michael DeHaan <michael.dehaan@gmail.com> - 0.5-0
- Release of 0.5

* Wed May 23 2012 Michael DeHaan <michael.dehaan@gmail.com> - 0.4-0
- Release of 0.4

* Mon Apr 23 2012 Michael DeHaan <michael.dehaan@gmail.com> - 0.3-1
- Release of 0.3

* Tue Apr  3 2012 John Eckersberg <jeckersb@redhat.com> - 0.0.2-1
- Release of 0.0.2

* Sat Mar 10 2012  <tbielawa@redhat.com> - 0.0.1-1
- Release of 0.0.1
