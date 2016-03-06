install
cdrom
text
lang en_GB.UTF-8
keyboard --vckeymap=uk
timezone --utc UTC
auth --enableshadow --enablemd5
selinux --disabled
firewall --disabled
eula --agreed
reboot --eject

ignoredisk --only-use=sda

# Hint: To generate an encrypted password run grub2-mkpasswd-pbkdf2
bootloader --location=mbr --iscrypted

zerombr
clearpart --all --initlabel
part /boot --fstype ext4 --size=256
part pv.01 --size=1 --grow
volgroup rootvg pv.01
logvol /              --vgname=rootvg --name=root        --fstype=ext4                                 --size=5120
logvol /home          --vgname=rootvg --name=home        --fstype=ext4 --fsoptions=nodev               --size=2048
logvol /tmp           --vgname=rootvg --name=tmp         --fstype=ext4 --fsoptions=nodev,nosuid,noexec --size=5120
logvol /usr           --vgname=rootvg --name=usr         --fstype=ext4                                 --size=10240
logvol /var           --vgname=rootvg --name=var         --fstype=ext4                                 --size=5120
logvol /var/log       --vgname=rootvg --name=varlog      --fstype=ext4                                 --size=2048
logvol /var/log/audit --vgname=rootvg --name=varlogaudit --fstype=ext4                                 --size=2048
logvol /opt           --vgname=rootvg --name=opt         --fstype=ext4                                 --size=5120

# Hint: To generate this encrypted password run the following:
# python -c "import string; import random; import crypt; seed = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(16)); print(crypt.crypt('your_password_in_here', '$6$' + seed))"
rootpw --iscrypted **INSERTPASSWORD**

user --name=packer  --password=packer
user --name=vagrant --password=vagrant

%packages --nobase
@core
-wpa_supplicant
%end

%addon com_redhat_kdump --disable
%end

%post --log=/root/post-install.log

echo "/tmp /var/tmp none bind 0 0" >> /etc/fstab
echo "tmpfs /dev/shm tmpfs nodev,nosuid,noexec 0 0" >> /etc/fstab

cat > /etc/modprobe.d/CIS.conf << EOF
install cramfs /bin/true
install freevxfs /bin/true
install jffs2 /bin/true
install hfs /bin/true
install hfsplus /bin/true
install squashfs /bin/true
install udf /bin/true
EOF

rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7

# Remove SSH host keys so that they'll be regenerated on template instantiation
rm -f /etc/ssh/ssh_host_*_key*

# Disable IPV6
cat > /etc/sysctl.d/disable_ipv6.conf << EOF
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
EOF

for part in / /boot /home /tmp /usr /var /var/log /var/log/audit; do
    cat /dev/zero > "${part}/filler.txt"
    rm -f "${part}/filler.txt"
done

for arg in $(cat /proc/cmdline); do
  case "${arg}" in
      ks=*)
          HTTP_SERVER=$(echo "${arg}" | awk -F/ '{ print $3 }')
          ;;
  esac
done

echo "HTTP_SERVER=${HTTP_SERVER}" >> /root/post-install.log

rpm -ivh https://repo.saltstack.com/yum/redhat/salt-repo-2015.8.el7.noarch.rpm
yum -t -y -e 0 install salt-minion

cat > /etc/sudoers.d/packer << EOF
Defaults:packer !requiretty
packer ALL=(ALL) NOPASSWD: ALL
EOF

cat > /etc/sudoers.d/vagrant << EOF
Defaults:vagrant !requiretty
vagrant ALL=(ALL) NOPASSWD: ALL
EOF

mkdir /home/vagrant/.ssh
chmod 0700 /home/vagrant/.ssh
cd /home/vagrant/.ssh
curl -o authorized_keys http://${HTTP_SERVER}/vagrant.pub
chmod 0600 authorized_keys
chown -R vagrant:vagrant /home/vagrant

rm -f /etc/yum.repos.d/*
#rm -f /etc/sysconfig/network-scripts/ifcfg-en*

mkdir -p /usr/local/bin/
curl -o /usr/local/bin/bootstrap.py http://${HTTP_SERVER}/bootstrap.py
chmod 700 /usr/local/bin/bootstrap.py
chown root:root /usr/local/bin/bootstrap.py

cat > /usr/lib/systemd/system/bootstrap.service << EOF
[Unit]
Description=Custom Bootstrap
After=rc-local.service syslog.target systemd-sysctl.service network.target

[Service]
Type=idle
ExecStart=/usr/local/bin/bootstrap.py

[Install]
WantedBy=multi-user.target
EOF

systemctl enable bootstrap.service

%end
