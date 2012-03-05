%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Summary: Minimal SSH command and control
Name: ansible
Version: 1.0
Release: 1
Source0: ansible-%{version}.tar.gz
License: MIT
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Url: http://github.com/mpdehaan/ansible/
BuildRequires: asciidoc

%description
Ansible is a extra-simple tool/API for doing 'parallel remote things' over SSH
executing commands, running "modules", or executing larger 'playbooks' that
can serve as a configuration management or deployment system.

%prep
%setup -n %{name}-%{version}

%build
python setup.py build
make docs

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
mkdir -p $RPM_BUILD_ROOT/etc/ansible/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%doc README.md AUTHORS.md PKG-INFO
%defattr(-,root,root)
%{_mandir}/man1/*.gz
%{_mandir}/man5/*.gz
%{python_sitelib}/*
%{_bindir}/ansible*
%{_datadir}/ansible/*
%{_sysconfdir}/ansible/

%changelog
* Mon Mar  5 2012 Seth Vidal <skvidal at fedoraproject.org>
- spec file

