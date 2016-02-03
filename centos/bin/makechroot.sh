#!/bin/bash

# Make a chroot area that can be used as a disposable environment e.g. testing, builds, etc.

# Tested on Centos 7 (7.1.1503 and 7.2.1511)

# Clear any previous version down
#
rm -rf /var/tmp/chroot/
mkdir -p /var/tmp/chroot/
cd /var/tmp/chroot

# Initialise an rpm db in the chroot
#
rpm --root=/var/tmp/chroot/ --rebuilddb

# Pull down release rpm and install in chroot
#
yum install wget
wget http://mirror.centos.org/centos-7/7/os/x86_64/Packages/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm
rpm --root=/var/tmp/chroot/ --nodeps -i centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm

# Tidy up and prep by copying in my repos
#
rm -f centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm
rm -f /var/tmp/chroot/etc/yum.repos.d/*
cp -p /etc/yum.repos.d/* /var/tmp/chroot/etc/yum.repos.d/

# Install yum plus pre-reqs and a few build tools
#
yum --installroot=/var/tmp/chroot/ update
yum --installroot=/var/tmp/chroot/ install -y yum
yum --installroot=/var/tmp/chroot/ install -y ruby-devel gcc rpm-build bind-utils wget openssl shadow-utils

# Sort out name resolution
#
for i in /etc/hosts /etc/nsswitch.conf /etc/resolv.conf
do
  cp -p ${i} /var/tmp/chroot/${i}
done

# Few home items for root
#
mkdir -p /var/tmp/chroot/root/
cat <<EOF > /var/tmp/chroot/root/.bashrc
export PS1="ChR00t> "
set -o vi
EOF

# Sort out some random number generators (e.g. for SSL)
#
mknod -m 444 /var/tmp/chroot/dev/random c 1 8
mknod -m 444 /var/tmp/chroot/dev/urandom c 1 9

# Go straight to jail. Do not pass GO.
#
chroot /var/tmp/chroot/ /bin/bash
exit
