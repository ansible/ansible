Name: ansible
Release: 1%{?dist}
Summary: Minimal SSH command and control
Version: 0.5

Group: Development/Libraries
License: GPLv3+
Source0: https://github.com/downloads/ansible/ansible/%{name}-%{version}.tar.gz
Url: http://ansible.github.com

BuildArch: noarch
BuildRequires: python2-devel

Requires: PyYAML
Requires: python-paramiko
Requires: python-jinja2

%description
Ansible is a radically simple model-driven configuration management,
multi-node deployment, and remote task execution system. Ansible works
over SSH and does not require any software or daemons to be installed
on remote nodes. Extension modules can be written in any language and
are transferred to managed machines automatically.

%prep
%setup -q

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --root=$RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/etc/ansible/
cp examples/hosts $RPM_BUILD_ROOT/etc/ansible/
mkdir -p $RPM_BUILD_ROOT/%{_mandir}/man1/
cp -v docs/man/man1/*.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/ansible
cp -v library/* $RPM_BUILD_ROOT/%{_datadir}/ansible/

%files
%{python_sitelib}/ansible*
%{_bindir}/ansible*
%{_datadir}/ansible
%config(noreplace) %{_sysconfdir}/ansible
%doc README.md PKG-INFO COPYING
%doc %{_mandir}/man1/ansible*

%changelog
* Wed Jul 4 2012 Michael DeHaan <michael.dehaan@gmail.com> - 0.5-0
- Release of 0.5

* Tue Jun 12 2012 Tim Bielawa <tbielawa@redhat.com> - 0.4.1-1
- Release of 0.4.1 (bugfixes)

* Wed May 23 2012 Michael DeHaan <michael.dehaan@gmail.com> - 0.4-0
- Release of 0.4

* Tue May  1 2012 Tim Bielawa <tbielawa@redhat.com> - 0.3.1-1
- Release of 0.3.1. Mostly packaging related changes.

* Mon Apr 23 2012 Michael DeHaan <michael.dehaan@gmail.com> - 0.3-1
- Release of 0.3

* Tue Apr  3 2012 John Eckersberg <jeckersb@redhat.com> - 0.0.2-1
- Release of 0.0.2

* Sat Mar 10 2012  <tbielawa@redhat.com> - 0.0.1-1
- Release of 0.0.1
