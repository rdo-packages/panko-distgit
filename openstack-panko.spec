# Macros for py2/py3 compatibility
%if 0%{?fedora} || 0%{?rhel} > 7
%global pyver %{python3_pkgversion}
%else
%global pyver 2
%endif

%global pyver_bin python%{pyver}
%global pyver_sitelib %python%{pyver}_sitelib
%global pyver_install %py%{pyver}_install
%global pyver_build %py%{pyver}_build
# End of macros for py2/py3 compatibility
%global pypi_name panko
%global with_doc %{!?_without_doc:1}%{?_without_doc:0}
%{!?upstream_version: %global upstream_version %{version}%{?milestone}}

%global common_desc OpenStack Panko provides API to store events from OpenStack components.


Name:           openstack-panko
Version:        6.0.0
Release:        1%{?dist}
Summary:        Panko provides Event storage and REST API

License:        ASL 2.0
URL:            http://github.com/openstack/panko
Source0:        https://tarballs.openstack.org/%{pypi_name}/%{pypi_name}-%{upstream_version}.tar.gz
#

Source1:        %{pypi_name}-dist.conf
Source2:        %{pypi_name}.logrotate
BuildArch:      noarch

BuildRequires:  python%{pyver}-setuptools
BuildRequires:  python%{pyver}-pbr
BuildRequires:  python%{pyver}-devel
BuildRequires:  openstack-macros

%description
HTTP API to store events.

%package -n     python%{pyver}-%{pypi_name}
Summary:        OpenStack panko python libraries
%{?python_provide:%python_provide python%{pyver}-%{pypi_name}}

Requires:       python%{pyver}-debtcollector >= 1.2.0
Requires:       python%{pyver}-tenacity >= 3.1.0
Requires:       python%{pyver}-keystonemiddleware >= 4.0.0
Requires:       python%{pyver}-oslo-config >= 2:3.9.0
Requires:       python%{pyver}-oslo-db >= 4.1.0
Requires:       python%{pyver}-oslo-i18n >= 2.1.0
Requires:       python%{pyver}-oslo-log >= 1.14.0
Requires:       python%{pyver}-oslo-middleware >= 3.10.0
Requires:       python%{pyver}-oslo-policy >= 0.5.0
Requires:       python%{pyver}-oslo-reports >= 0.6.0
Requires:       python%{pyver}-oslo-utils >= 3.5.0
Requires:       python%{pyver}-pecan >= 1.0.0
Requires:       python%{pyver}-six >= 1.9.0
Requires:       python%{pyver}-sqlalchemy >= 1.0.10
Requires:       python%{pyver}-alembic >= 0.7.6
Requires:       python%{pyver}-stevedore >= 1.9.0
Requires:       python%{pyver}-webob >= 1.2.3
Requires:       python%{pyver}-wsme
Requires:       python%{pyver}-dateutil >= 2.4.2
Requires:       python%{pyver}-pbr

# Handle python2 exception
%if %{pyver} == 2
Requires:       python-lxml
Requires:       python-paste
Requires:       python-paste-deploy
Requires:       python-sqlalchemy-utils
Requires:       PyYAML
%else
Requires:       python%{pyver}-lxml
Requires:       python%{pyver}-paste
Requires:       python%{pyver}-paste-deploy
Requires:       python%{pyver}-sqlalchemy-utils
Requires:       python%{pyver}-PyYAML
%endif

%description -n   python%{pyver}-%{pypi_name}
%{common_desc}

This package contains the Panko python library.


%package        api

Summary:        OpenStack panko api

Requires:       %{name}-common = %{version}-%{release}


%description api
%{common_desc}

This package contains the Panko API service.

%package        common
Summary:        Components common to all OpenStack panko services

# Config file generation
BuildRequires:    python%{pyver}-oslo-config >= 2:2.6.0
BuildRequires:    python%{pyver}-oslo-concurrency
BuildRequires:    python%{pyver}-oslo-db
BuildRequires:    python%{pyver}-oslo-log
BuildRequires:    python%{pyver}-oslo-messaging
BuildRequires:    python%{pyver}-oslo-policy
BuildRequires:    python%{pyver}-oslo-reports
BuildRequires:    python%{pyver}-oslo-service
BuildRequires:    python%{pyver}-tenacity
BuildRequires:    python%{pyver}-werkzeug

Requires:       python%{pyver}-panko = %{version}-%{release}
Requires:       openstack-ceilometer-common


%description    common
%{common_desc}

%package -n python%{pyver}-panko-tests
Summary:       Panko tests
%{?python_provide:%python_provide python%{pyver}-panko-tests}
Requires:       python%{pyver}-panko = %{version}-%{release}

%description -n python%{pyver}-%{pypi_name}-tests
This package contains the Panko test files.

%if 0%{?with_doc}
%package doc
Summary:          Documentation for OpenStack panko

Requires:         python%{pyver}-panko = %{version}-%{release}
BuildRequires:    python%{pyver}-sphinx
BuildRequires:    python%{pyver}-oslo-sphinx >= 2.2.0
BuildRequires:    openstack-macros

%description      doc
%{common_desc}

This package contains documentation files for Panko.
%endif


%prep
%setup -q -n %{pypi_name}-%{upstream_version}

find . \( -name .gitignore -o -name .placeholder \) -delete

find panko -name \*.py -exec sed -i '/\/usr\/bin\/env python/{d;q}' {} +

sed -i '/setup_requires/d; /install_requires/d; /dependency_links/d' setup.py

%py_req_cleanup


%build

# Generate config file
PYTHONPATH=. oslo-config-generator-%{pyver} --config-file=etc/panko/panko-config-generator.conf

%{pyver_build}

# Programmatically update defaults in sample config
# which is installed at /etc/panko/panko.conf
# TODO: Make this more robust
# Note it only edits the first occurrence, so assumes a section ordering in sample
# and also doesn't support multi-valued variables.
while read name eq value; do
  test "$name" && test "$value" || continue
  sed -i "0,/^# *$name=/{s!^# *$name=.*!#$name=$value!}" etc/panko/panko.conf
done < %{SOURCE1}


%install

%{pyver_install}

mkdir -p %{buildroot}/%{_sysconfdir}/sysconfig/
mkdir -p %{buildroot}/%{_sysconfdir}/panko/
mkdir -p %{buildroot}/%{_var}/log/%{name}

install -p -D -m 640 %{SOURCE1} %{buildroot}%{_datadir}/panko/panko-dist.conf
install -p -D -m 640 etc/panko/panko.conf %{buildroot}%{_sysconfdir}/panko/panko.conf
install -p -D -m 640 etc/panko/api_paste.ini %{buildroot}%{_sysconfdir}/panko/api_paste.ini

#TODO(prad): build the docs at run time, once the we get rid of postgres setup dependency

# Setup directories
install -d -m 755 %{buildroot}%{_sharedstatedir}/panko
install -d -m 755 %{buildroot}%{_sharedstatedir}/panko/tmp
install -d -m 755 %{buildroot}%{_localstatedir}/log/panko

# Install logrotate
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

# Remove all of the conf files that are included in the buildroot/usr/etc dir since we installed them above
rm -f %{buildroot}/usr/etc/panko/*

%pre common
getent group panko >/dev/null || groupadd -r panko
if ! getent passwd panko >/dev/null; then
  useradd -r -g panko -G panko,nobody -d %{_sharedstatedir}/panko -s /sbin/nologin -c "OpenStack panko Daemons" panko
fi
# Add ceilometer user to panko group to read panko config
usermod -a -G panko ceilometer
exit 0


%files -n python%{pyver}-panko
%{pyver_sitelib}/panko
%{pyver_sitelib}/panko-*.egg-info

%exclude %{pyver_sitelib}/panko/tests

%files -n python%{pyver}-panko-tests
%license LICENSE
%{pyver_sitelib}/panko/tests

%files api
%defattr(-,root,root,-)
%{_bindir}/panko-api
%{_bindir}/panko-dbsync
%{_bindir}/panko-expirer

%files common
%dir %{_sysconfdir}/panko
%attr(-, root, panko) %{_datadir}/panko/panko-dist.conf
%config(noreplace) %attr(-, root, panko) %{_sysconfdir}/panko/panko.conf
%config(noreplace) %attr(-, root, panko) %{_sysconfdir}/panko/api_paste.ini
%config(noreplace) %attr(-, root, panko) %{_sysconfdir}/logrotate.d/%{name}
%dir %attr(0755, panko, root)  %{_localstatedir}/log/panko

%defattr(-, panko, panko, -)
%dir %{_sharedstatedir}/panko
%dir %{_sharedstatedir}/panko/tmp


%if 0%{?with_doc}
%files doc
%doc doc/source/
%endif


%changelog
* Wed Apr 10 2019 RDO <dev@lists.rdoproject.org> 6.0.0-1
- Update to 6.0.0

* Fri Mar 22 2019 RDO <dev@lists.rdoproject.org> 6.0.0-0.1.0rc1
- Update to 6.0.0.0rc1

