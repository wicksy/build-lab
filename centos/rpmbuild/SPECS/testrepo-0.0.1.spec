Name:           testrepo
Version:	      0.0.1
Release:        1%{?dist}
Summary:        RPM package containing test repo and GPG key

Group:          Me
License:        GPLv3
URL:            URL
Source0:        $RPM_BUILD_ROOT/SOURCES/testrepo-0.0.1.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
Installs a custom repo and key

%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/yum.repos.d/
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/pki/rpm-gpg/
cp -p test.repo $RPM_BUILD_ROOT%{_sysconfdir}/yum.repos.d/
cp -p test-gpg-key $RPM_BUILD_ROOT%{_sysconfdir}/pki/rpm-gpg/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
/etc/yum.repos.d/test.repo
/etc/pki/rpm-gpg/test-gpg-key

%pre
echo "Commands to run before package installed"
exit 0

%post
echo "Commands to run after the package is installed"
exit 0

%preun
echo "Commmands to run before uninstalling the package"
exit 0

%postun
echo "Commands to run after uninstalling the package"
exit 0

%changelog
* Fri Dec 05 2014 Martin Wicks <wicksy@wicksy.com> 0.0.1
- This is a custom rpm for a test repo and key
