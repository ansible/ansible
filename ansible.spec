%if 0%{?rhel} <= 5
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
%endif

Name: ansible
Release: 1%{?dist}
Summary: Minimal SSH command and control
Version: 0.0.2

Group: Development/Libraries
License: GPLv3
Source0: https://github.com/downloads/ansible/ansible/%{name}-%{version}.tar.gz
Url: http://ansible.github.com

BuildArch: noarch
BuildRequires: python2-devel

Requires: python-paramiko
Requires: python-jinja2

%description

Ansible is a radically simple deployment, model-driven configuration
management, and command execution framework. What you get is both an
extra-simple tool and an API for doing 'parallel remote things' over
SSH.

Ansible modules are reusable units of magic that can be used by the
Ansible API, or by the ansible or ansible-playbook programs. Modules
can be written in any language. Ansible ships with a standard library
of modules.


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

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{python_sitelib}/ansible*
%{_bindir}/ansible*
%{_datadir}/ansible
%config(noreplace) %{_sysconfdir}/ansible/*
%doc README.md PKG-INFO
%doc %{_mandir}/man1/ansible*


%changelog
* Tue Apr  3 2012 John Eckersberg <jeckersb@redhat.com> - 0.0.2-1
- Release of 0.0.2

* Sat Mar 10 2012  <tbielawa@redhat.com> - 0.0.1-1
- Release of 0.0.1
