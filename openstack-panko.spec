%global pypi_name panko
%global with_doc %{!?_without_doc:1}%{?_without_doc:0}
%{!?upstream_version: %global upstream_version %{version}%{?milestone}}

%global common_desc OpenStack Panko provides API to store events from OpenStack components.

%global common_desc_doc \
OpenStack Panko provides services to measure and \
collect events from OpenStack components.


Name:           openstack-panko
Version:        XXX
Release:        XXX
Summary:        Panko provides Event storage and REST API

License:        ASL 2.0
URL:            http://github.com/openstack/panko
Source0:        https://tarballs.openstack.org/%{pypi_name}/%{pypi_name}-%{upstream_version}.tar.gz
Source1:        %{pypi_name}-dist.conf
Source2:        %{pypi_name}.logrotate
BuildArch:      noarch

BuildRequires:  python-setuptools
BuildRequires:  python-pbr
BuildRequires:  python2-devel
BuildRequires:  openstack-macros

%description
HTTP API to store events.

%package -n     python-%{pypi_name}
Summary:        OpenStack panko python libraries

Requires:       python-debtcollector >= 1.2.0
Requires:       python-tenacity >= 3.1.0
Requires:       python-lxml
Requires:       python-keystonemiddleware >= 4.0.0
Requires:       python-oslo-config >= 2:3.9.0
Requires:       python-oslo-db >= 4.1.0
Requires:       python-oslo-i18n >= 2.1.0
Requires:       python-oslo-log >= 1.14.0
Requires:       python-oslo-middleware >= 3.10.0
Requires:       python-oslo-policy >= 0.5.0
Requires:       python-oslo-reports >= 0.6.0
Requires:       python-oslo-utils >= 3.5.0
Requires:       python-paste
Requires:       python-paste-deploy
Requires:       python-pecan >= 1.0.0
Requires:       python-six >= 1.9.0
Requires:       python-sqlalchemy >= 1.0.10
Requires:       python-sqlalchemy-utils
Requires:       python-stevedore >= 1.9.0
Requires:       PyYAML
Requires:       python-webob >= 1.2.3
Requires:       python-wsme
Requires:       python-dateutil >= 2.4.2
Requires:       python-pbr

%description -n   python-%{pypi_name}
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
BuildRequires:    python-oslo-config >= 2:2.6.0
BuildRequires:    python-oslo-concurrency
BuildRequires:    python-oslo-db
BuildRequires:    python-oslo-log
BuildRequires:    python-oslo-messaging
BuildRequires:    python-oslo-policy
BuildRequires:    python-oslo-reports
BuildRequires:    python-oslo-service
BuildRequires:    python-werkzeug

Requires:       python-panko = %{version}-%{release}
Requires:       openstack-ceilometer-common


%description    common
%{common_desc_doc}

%package -n python-panko-tests
Summary:       Panko tests
Requires:       python-panko = %{version}-%{release}

%description -n python-%{pypi_name}-tests
This package contains the Panko test files.

%if 0%{?with_doc}
%package doc
Summary:          Documentation for OpenStack panko

Requires:         python-panko = %{version}-%{release}
BuildRequires:    python-sphinx
BuildRequires:    python-oslo-sphinx >= 2.2.0
BuildRequires:    openstack-macros

%description      doc
%{common_desc_doc}

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
PYTHONPATH=. oslo-config-generator --config-file=etc/panko/panko-config-generator.conf

%py2_build

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

%py2_install

# Create fake egg-info for the tempest plugin
%global service panko
%py2_entrypoint %{service} %{service}

mkdir -p %{buildroot}/%{_sysconfdir}/sysconfig/
mkdir -p %{buildroot}/%{_sysconfdir}/panko/
mkdir -p %{buildroot}/%{_var}/log/%{name}

install -p -D -m 640 %{SOURCE1} %{buildroot}%{_datadir}/panko/panko-dist.conf
install -p -D -m 640 etc/panko/panko.conf %{buildroot}%{_sysconfdir}/panko/panko.conf
install -p -D -m 640 etc/panko/api_paste.ini %{buildroot}%{_sysconfdir}/panko/api_paste.ini

#TODO(prad): build the docs at run time, once the we get rid of postgres setup dependency

# Configuration
cp -R etc/panko/policy.json %{buildroot}/%{_sysconfdir}/panko

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


%files -n python-panko
%{python2_sitelib}/panko
%{python2_sitelib}/panko-*.egg-info

%exclude %{python2_sitelib}/panko/tests

%files -n python-panko-tests
%license LICENSE
%{python2_sitelib}/panko/tests
%{python2_sitelib}/%{service}_tests.egg-info

%files api
%defattr(-,root,root,-)
%{_bindir}/panko-api
%{_bindir}/panko-dbsync
%{_bindir}/panko-expirer

%files common
%dir %{_sysconfdir}/panko
%attr(-, root, panko) %{_datadir}/panko/panko-dist.conf
%config(noreplace) %attr(-, root, panko) %{_sysconfdir}/panko/policy.json
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
* Fri Jul 29 2016 Pradeep Kilambi <pkilambi@redhat.com> - 1.0.0.0b1-1
- initial spec


