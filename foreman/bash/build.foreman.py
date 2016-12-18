#!/usr/bin/python

import os, subprocess, sys, time

with open('/tmp/build.foreman', 'w') as w:
        os.chmod('/tmp/build.foreman', 0700)
        w.write("""\
#!/bin/bash

shorthost="${1}"

if [[ `/bin/echo "${shorthost}" | /usr/bin/tr -d ' '` == "" ]] ; then
        echo "Enter short host name e.g. testhost"
        read shorthost
        if [[ `/bin/echo "${shorthost}" | /usr/bin/tr -d ' '` == "" ]] ; then
                /bin/echo "No host name specified"
                exit 100
        fi
else
        echo "Using host name ${shorthost}"
fi

domain="localdomain"
longhost="${shorthost}.${domain}"
hostip=`/bin/hostname --all-ip-addresses`
progname=`/bin/basename "${0}"`
logfile="/tmp/${progname}.$$.out"

/bin/echo "Starting ${progname} script"
/bin/echo "Logging session to ${logfile}"

set -x

exec 1>${logfile}
exec 2>&1

/bin/chmod 600 ${logfile}

/bin/echo "Fixing hostname"
/bin/sed -i "s/HOSTNAME=.*/HOSTNAME=${longhost}/g" /etc/sysconfig/network
/bin/hostname "${longhost}"

/bin/echo "${hostip} ${longhost} ${shorthost}" >> /etc/hosts

# Restart syslog to pick up new hostname
/sbin/service rsyslog restart

/bin/echo "Fixing resolv.conf" 
/bin/cat > /etc/resolv.conf << EOF
search localdomain
search eu-west-1.compute.internal
nameserver dns1.localdomain
nameserver dns2.localdomain
nameserver dns3.localdomain
EOF

/usr/bin/chattr +i /etc/resolv.conf

/bin/echo "Creating proxy.sh" 
/bin/cat > /etc/profile.d/proxy.sh << EOF
export http_proxy=http://proxy.localdomain:8080
export ftp_proxy=http://proxy.localdomain:8080
export https_proxy=http://proxy.localdomain:8080
export HTTP_PROXY=http://proxy.localdomain:8080
export FTP_PROXY=http://proxy.localdomain:8080
export no_proxy="localhost,127.0.0.1"
export EC2_JVM_ARGS="-Dhttps.proxyHost=proxy.localdomain -Dhttps.proxyPort=8080"
EOF

. /etc/profile.d/proxy.sh

/bin/echo "Running yum udpate" 
#/usr/bin/yum -t -y -e 0 update

/bin/echo "Adding proxy to yum.conf" 
/bin/echo "proxy=http://proxy.localdomain:8080" >> /etc/yum.conf

/bin/echo "Enabling RHEL specific repos"
/usr/bin/yum-config-manager --enable rhui-REGION-rhel-server-releases-optional rhui-REGION-rhel-server-rhscl

/bin/echo "Installing epel repo"
# install EPEL
/bin/rpm -Uvh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm

/bin/echo "Installing puppetlabs repo"
# install Puppetlabs
/bin/rpm -Uvh http://yum.puppetlabs.com/puppetlabs-release-el-6.noarch.rpm

/bin/echo "Installing foreman repo"
/usr/bin/yum -y install http://yum.theforeman.org/releases/1.6/el6/x86_64/foreman-release.rpm

/bin/echo "Rebuilding yum caches"
/usr/bin/yum -y clean all
/usr/bin/yum -y makecache

/bin/echo "Installing foreman installer"
/usr/bin/yum -y install foreman-installer

export HOME=/root

/bin/echo "Installing and configuring foreman"
/usr/sbin/foreman-installer -v --enable-foreman-compute-ec2

/bin/echo "Installing gems for foreman API"
/usr/bin/gem install json-tools -V

/bin/echo "Updating httpd to use proxies"
/bin/cat >> /etc/sysconfig/httpd << EOF
export http_proxy=http://proxy.localdomain:8080
export https_proxy=http://proxy.localdomain:8080
export ftp_proxy=http://proxy.localdomain:8080
EOF

/bin/sleep 30

/bin/echo "Restarting httpd"
/sbin/service httpd restart 

/bin/sleep 10

/bin/echo "Forcing puppet agent run to gather facts and register host"
/usr/bin/puppet agent -t -v

/bin/sleep 60

exit 0
""")

with open('/tmp/build.foreman.objects', 'w') as w:
        os.chmod('/tmp/build.foreman.objects', 0700)
        w.write("""\
#!/bin/bash

fail () {
	code=${1}
	shift
	text=${*}
	echo ${text}
	exit ${code}
}

progname=`/bin/basename "${0}"`
logfile="/tmp/${progname}.$$.out"
foreman_url="http://localhost"

/bin/echo "Starting ${progname} script"
/bin/echo "Logging session to ${logfile}"

set -x

exec 1>${logfile}
exec 2>&1

/bin/chmod 600 ${logfile}

inlog=`/bin/ls -1tr /tmp/build.foreman.[0-9]*.out 2>/dev/null \
  | /usr/bin/tr -d ' ' \
  | /usr/bin/tail -1`

[[ `/bin/echo "${inlog}"` == "" ]] && fail 100 "Cannot find any foreman build log"

[[ ! -s ${inlog} ]] && fail 110 "Foreman build log is invalid (${inlog})"

/bin/echo "Foreman build log is ${inlog}"
/bin/echo "Extracting admin credentials"

adminuser=`/bin/cat ${inlog} \
            | /bin/sed -r "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]//g" \
            | /bin/awk '/Initial credentials are/ {print $(NF-2)}'`

adminpass=`/bin/cat ${inlog} \
            | /bin/sed -r "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]//g" \
            | /bin/awk '/Initial credentials are/ {print $NF}'`

/bin/echo "Login: ${adminuser}" 
/bin/echo "Password: ${adminpass}"

/bin/echo "Credentials extracted"

access_key="AWS_ACCESS_KEY"
secret_key="AWS_SECRET_KEY"

/bin/echo "Creating Compute Resource (EC2)"

out=$(/usr/bin/curl -s -H "Accept:application/json" -H "Content-Type:application/json" \
     -k -u ${adminuser}:${adminpass} \
     -d '
{
  "compute_resource": {
    "name": "ec2-eu-west-1",
    "region": "eu-west-1",
    "provider": "EC2",
    "user": "'${access_key}'",
    "password": "'${secret_key}'"
  }
}
	' \
	${foreman_url}/api/compute_resources \
		| /usr/bin/python -mjson.tool \
	)

id=`/bin/echo ${out} \
	| /usr/bin/python -mjson.tool \
	| /bin/awk -F':' '/\"id\":/ {print $2}' \
	| /usr/bin/tr -d ', '`

/bin/echo "Compute resource id is ${id}"

/bin/echo "Creating RHEL 6.5 image"
out=$(/usr/bin/curl -s -H "Accept:application/json" -H "Content-Type:application/json" \
     -k -u ${adminuser}:${adminpass} \
     -d '
{
  "image": {
    "name": "RHEL Server 6.5",
    "operatingsystem_id": "1",
    "compute_resource_id": "'${id}'",
    "architecture_id": "1",
    "username": "ec2-user",
    "uuid": "ami-8cfc51fb",
    "user_data": "0"
  }
}
	' \
	${foreman_url}/api/compute_resources/${id}/images \
		| /usr/bin/python -mjson.tool \
	)

/bin/echo ${out} \
	| /usr/bin/python -mjson.tool

/bin/echo "Creating subnet"
out=$(/usr/bin/curl -s -H "Accept:application/json" -H "Content-Type:application/json" \
     -k -u ${adminuser}:${adminpass} \
     -d '
{
  "subnet": {
    "name": "Test subnet A",
    "network": "192.168.1.0",
    "mask": "255.255.255.0",
    "dns_secondary": "192.168.1.254"
  }
}
	' \
	${foreman_url}/api/subnets \
		| /usr/bin/python -mjson.tool \
	)

/bin/echo ${out} \
	| /usr/bin/python -mjson.tool

/bin/echo "Updating default OS (marking as 64bit)"
out=$(/usr/bin/curl -s -H "Accept:application/json" -H "Content-Type:application/json" \
     -X PUT \
     -k -u ${adminuser}:${adminpass} \
     -d '
{
  "operatingsystem": {
    "name": "RedHat",
    "description": "RHEL Server 6.5",
    "architecture_ids": ["", "1", ""]
  }
}
	' \
	${foreman_url}/api/operatingsystems/1 \
		| /usr/bin/python -mjson.tool \
	)

/bin/echo ${out} \
	| /usr/bin/python -mjson.tool

/bin/echo "Creating test host group"
out=$(/usr/bin/curl -s -H "Accept:application/json" -H "Content-Type:application/json" \
     -k -u ${adminuser}:${adminpass} \
     -d '
{
  "hostgroup": {
    "name": "test",
    "environment_id": "1",
    "puppet_ca_proxy_id": "1",
    "puppet_proxy_id": "1",
    "domain_id": "1",
    "subnet_id": "1",
    "architecture_id": "1",
    "operatingsystem_id": "1"
  }
}
	' \
	${foreman_url}/api/hostgroups \
		| /usr/bin/python -mjson.tool \
	)

/bin/echo ${out} \
	| /usr/bin/python -mjson.tool

/bin/echo "Creating finish template"
out=$(/usr/bin/curl -s -H "Accept:application/json" -H "Content-Type:application/json" \
     -k -u ${adminuser}:${adminpass} \
     -d '
{
  "config_template": {
    "name": "REDHAT",
    "template": "exit 0",
    "snippet": "0",
    "template_kind_id": "5",
    "operatingsystem_ids": ["", "1"],
    "template_combinations_attributes": {
	"0": {
		"hostgroup_id": "1",
		"environment_id": "1"
	}
    }
  }
}
	' \
	${foreman_url}/api/config_templates \
		| /usr/bin/python -mjson.tool \
	)

/bin/echo "Base object build complete"
exit 0
""")

with open('/tmp/build.foreman.stub', 'w') as w:
        os.chmod('/tmp/build.foreman.stub', 0700)
        w.write("""\
#!/bin/bash

host=${1}

progname=`/bin/basename "${0}"`
logfile="/tmp/${progname}.$$.out"

set -x

exec 1>${logfile}
exec 2>&1

/bin/chmod 600 ${logfile}

while :
do
  /bin/grep 'END SSH HOST KEY FINGERPRINTS' /var/log/messages && break
  /bin/sleep 30
done

/tmp/build.foreman ${host}
/bin/sleep 60
/tmp/build.foreman.objects

exit 0
""")

