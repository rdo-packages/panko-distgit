%{!?sources_gpg: %{!?dlrn:%global sources_gpg 1} }
%global sources_gpg_sign 0x2426b928085a020d8a90d0d879ab7008d0896c8a
%global pypi_name panko
%global with_doc %{!?_without_doc:1}%{?_without_doc:0}
%{!?upstream_version: %global upstream_version %{version}%{?milestone}}

%global common_desc OpenStack Panko provides API to store events from OpenStack components.


Name:           openstack-panko
Version:        XXX
Release:        XXX
Summary:        Panko provides Event storage and REST API

License:        ASL 2.0
URL:            http://github.com/openstack/panko
Source0:        https://tarballs.openstack.org/%{pypi_name}/%{pypi_name}-%{upstream_version}.tar.gz
Source1:        %{pypi_name}-dist.conf
Source2:        %{pypi_name}.logrotate
# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
Source101:        https://tarballs.openstack.org/%{pypi_name}/%{pypi_name}-%{upstream_version}.tar.gz.asc
Source102:        https://releases.openstack.org/_static/%{sources_gpg_sign}.txt
%endif
BuildArch:      noarch

# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
BuildRequires:  /usr/bin/gpgv2
%endif

BuildRequires:  python3-setuptools
BuildRequires:  python3-pbr
BuildRequires:  python3-devel
BuildRequires:  openstack-macros

%description
HTTP API to store events.

%package -n     python3-%{pypi_name}
Summary:        OpenStack panko python libraries
%{?python_provide:%python_provide python3-%{pypi_name}}

Requires:       python3-debtcollector >= 1.2.0
Requires:       python3-tenacity >= 3.1.0
Requires:       python3-keystonemiddleware >= 5.1.0
Requires:       python3-oslo-config >= 2:3.9.0
Requires:       python3-oslo-db >= 4.1.0
Requires:       python3-oslo-i18n >= 2.1.0
Requires:       python3-oslo-log >= 4.3.0
Requires:       python3-oslo-middleware >= 3.10.0
Requires:       python3-oslo-policy >= 3.6.0
Requires:       python3-oslo-reports >= 0.6.0
Requires:       python3-oslo-utils >= 3.5.0
Requires:       python3-oslo-serialization >= 2.25.0
Requires:       python3-pecan >= 1.0.0
Requires:       python3-sqlalchemy >= 1.0.10
Requires:       python3-alembic >= 0.7.6
Requires:       python3-stevedore >= 1.9.0
Requires:       python3-webob >= 1.2.3
Requires:       python3-wsme >= 0.8
Requires:       python3-dateutil >= 2.4.2
Requires:       python3-pbr >= 2.0.0

Requires:       python3-lxml >= 2.3
Requires:       python3-paste
Requires:       python3-paste-deploy >= 1.5.0
Requires:       python3-sqlalchemy-utils
Requires:       python3-yaml >= 3.1.0
Requires:       python3-oslo-context >= 2.22.0

%description -n   python3-%{pypi_name}
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
BuildRequires:    python3-oslo-config >= 2:2.6.0
BuildRequires:    python3-oslo-concurrency
BuildRequires:    python3-oslo-db
BuildRequires:    python3-oslo-log
BuildRequires:    python3-oslo-messaging
BuildRequires:    python3-oslo-policy
BuildRequires:    python3-oslo-reports
BuildRequires:    python3-oslo-service
BuildRequires:    python3-tenacity
BuildRequires:    python3-werkzeug

Requires:       python3-panko = %{version}-%{release}
Requires:       openstack-ceilometer-common


%description    common
%{common_desc}

%package -n python3-panko-tests
Summary:       Panko tests
%{?python_provide:%python_provide python3-panko-tests}
Requires:       python3-panko = %{version}-%{release}

%description -n python3-%{pypi_name}-tests
This package contains the Panko test files.

%if 0%{?with_doc}
%package doc
Summary:          Documentation for OpenStack panko

Requires:         python3-panko = %{version}-%{release}
BuildRequires:    python3-sphinx
BuildRequires:    python3-oslo-sphinx >= 2.2.0
BuildRequires:    openstack-macros

%description      doc
%{common_desc}

This package contains documentation files for Panko.
%endif


%prep
# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
%{gpgverify}  --keyring=%{SOURCE102} --signature=%{SOURCE101} --data=%{SOURCE0}
%endif
%setup -q -n %{pypi_name}-%{upstream_version}

find . \( -name .gitignore -o -name .placeholder \) -delete

find panko -name \*.py -exec sed -i '/\/usr\/bin\/env python/{d;q}' {} +

sed -i '/setup_requires/d; /install_requires/d; /dependency_links/d' setup.py

%py_req_cleanup


%build

# Generate config file
PYTHONPATH=. oslo-config-generator --config-file=etc/panko/panko-config-generator.conf

%{py3_build}

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

%{py3_install}

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


%files -n python3-panko
%{python3_sitelib}/panko
%{python3_sitelib}/panko-*.egg-info

%exclude %{python3_sitelib}/panko/tests

%files -n python3-panko-tests
%license LICENSE
%{python3_sitelib}/panko/tests

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
