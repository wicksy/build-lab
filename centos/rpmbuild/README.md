### Example of building an rpm with rpmbuild

```
[rpmbuild@rh300vm rpmbuild]$ getent passwd rpmbuild
rpmbuild:x:502:504:RPM package builder:/home/rpmbuild:/bin/bash
[rpmbuild@rh300vm rpmbuild]$ id -a rpmbuild
uid=502(rpmbuild) gid=504(rpmbuild) groups=504(rpmbuild)
[rpmbuild@rh300vm rpmbuild]$ getent group rpmbuild
rpmbuild:x:504:
[rpmbuild@rh300vm rpmbuild]$

[rpmbuild@rh300vm rpmbuild]$ rpm -qa --last | awk '/Fri 05 Dec 2014/'
rpmdevtools-7.5-1.el6                         Fri 05 Dec 2014 07:38:04 PM GMT
fakeroot-1.12.2-22.2.el6                      Fri 05 Dec 2014 07:38:00 PM GMT
fakeroot-libs-1.12.2-22.2.el6                 Fri 05 Dec 2014 07:37:58 PM GMT
[rpmbuild@rh300vm rpmbuild]$

[rpmbuild@rh300vm rpmbuild]$ rpmbuild --clean SPECS/testrepo-0.0.1.spec
Executing(--clean): /bin/sh -e /var/tmp/rpm-tmp.pjWGp1
+ umask 022
+ cd /home/rpmbuild/rpmbuild/BUILD
+ rm -rf testrepo-0.0.1
+ exit 0
[rpmbuild@rh300vm rpmbuild]$

[rpmbuild@rh300vm rpmbuild]$ rpmbuild -ba -vv ./SPECS/testrepo-0.0.1.spec
Executing(%prep): /bin/sh -e /var/tmp/rpm-tmp.OpnNrm
+ umask 022
+ cd /home/rpmbuild/rpmbuild/BUILD
+ LANG=C
+ export LANG
+ unset DISPLAY
+ cd /home/rpmbuild/rpmbuild/BUILD
+ rm -rf testrepo-0.0.1
+ /usr/bin/gzip -dc /home/rpmbuild/rpmbuild/SOURCES/testrepo-0.0.1.tar.gz
+ /bin/tar -xf -
+ STATUS=0
+ '[' 0 -ne 0 ']'
+ cd testrepo-0.0.1
+ /bin/chmod -Rf a+rX,u+w,g-w,o-w .
+ exit 0
Executing(%build): /bin/sh -e /var/tmp/rpm-tmp.FcTUj1
+ umask 022
+ cd /home/rpmbuild/rpmbuild/BUILD
+ cd testrepo-0.0.1
+ LANG=C
+ export LANG
+ unset DISPLAY
+ exit 0
Executing(%install): /bin/sh -e /var/tmp/rpm-tmp.OGXkcG
+ umask 022
+ cd /home/rpmbuild/rpmbuild/BUILD
+ '[' /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386 '!=' / ']'
+ rm -rf /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386
++ dirname /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386
+ mkdir -p /home/rpmbuild/rpmbuild/BUILDROOT
+ mkdir /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386
+ cd testrepo-0.0.1
+ LANG=C
+ export LANG
+ unset DISPLAY
+ rm -rf /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386
+ mkdir -p /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386/etc/yum.repos.d/
+ mkdir -p /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386/etc/pki/rpm-gpg/
+ cp -p test.repo /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386/etc/yum.repos.d/
+ cp -p test-gpg-key /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386/etc/pki/rpm-gpg/
+ /usr/lib/rpm/find-debuginfo.sh --strict-build-id /home/rpmbuild/rpmbuild/BUILD/testrepo-0.0.1
+ /usr/lib/rpm/check-buildroot
+ /usr/lib/rpm/redhat/brp-compress
+ /usr/lib/rpm/redhat/brp-strip-static-archive /usr/bin/strip
+ /usr/lib/rpm/redhat/brp-strip-comment-note /usr/bin/strip /usr/bin/objdump
+ /usr/lib/rpm/brp-python-bytecompile
+ /usr/lib/rpm/redhat/brp-python-hardlink
+ /usr/lib/rpm/redhat/brp-java-repack-jars
Processing files: testrepo-0.0.1-1.el6.i686
D: /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386/etc/pki/rpm-gpg/test-gpg-key: ASCII text
D: /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386/etc/yum.repos.d/test.repo: ASCII text
Requires(rpmlib): rpmlib(CompressedFileNames) <= 3.0.4-1 rpmlib(FileDigests) <= 4.6.0-1 rpmlib(PayloadFilesHavePrefix) <= 4.0-1
Processing files: testrepo-debuginfo-0.0.1-1.el6.i686
Checking for unpackaged file(s): /usr/lib/rpm/check-files /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386
D:      execv(/usr/lib/rpm/check-files) pid 32309
D:      waitpid(32309) rc 32309 status 0
warning: Could not canonicalize hostname: rh300vm
D: fini      100664  1 (   0,   0)       896 /home/rpmbuild/rpmbuild/SPECS/testrepo-0.0.1.spec
D: fini      100664  1 (   0,   0)       239 /home/rpmbuild/rpmbuild/SOURCES/testrepo-0.0.1.tar.gz
GZDIO:       1 writes,     1524 total bytes in 0.000162 secs
D: Signature: size(180)+pad(4)
Wrote: /home/rpmbuild/rpmbuild/SRPMS/testrepo-0.0.1-1.el6.src.rpm
D: ========== relocations
D: fini      100644  1 (   0,   0)        13 /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386/etc/pki/rpm-gpg/test-gpg-key
D: fini      100644  1 (   0,   0)        15 /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386/etc/yum.repos.d/test.repo
XZDIO:       1 writes,      440 total bytes in 0.000048 secs
D: Signature: size(180)+pad(4)
Wrote: /home/rpmbuild/rpmbuild/RPMS/i686/testrepo-0.0.1-1.el6.i686.rpm
XZDIO:       1 writes,      124 total bytes in 0.000020 secs
D: Signature: size(180)+pad(4)
Wrote: /home/rpmbuild/rpmbuild/RPMS/i686/testrepo-debuginfo-0.0.1-1.el6.i686.rpm
Executing(%clean): /bin/sh -e /var/tmp/rpm-tmp.lhnhXR
+ umask 022
+ cd /home/rpmbuild/rpmbuild/BUILD
+ cd testrepo-0.0.1
+ rm -rf /home/rpmbuild/rpmbuild/BUILDROOT/testrepo-0.0.1-1.el6.i386
+ exit 0
[rpmbuild@rh300vm rpmbuild]$

[rpmbuild@rh300vm rpmbuild]$ rpm -qi -p RPMS/i686/testrepo-0.0.1-1.el6.i686.rpm
Name        : testrepo                     Relocations: (not relocatable)
Version     : 0.0.1                             Vendor: (none)
Release     : 1.el6                         Build Date: Fri 05 Dec 2014 07:59:12 PM GMT
Install Date: (not installed)               Build Host: rh300vm
Group       : Me                            Source RPM: testrepo-0.0.1-1.el6.src.rpm
Size        : 28                               License: GPLv3
Signature   : (none)
URL         : URL
Summary     : RPM package containing test repo and GPG key
Description :
Installs a custom repo and key
[rpmbuild@rh300vm rpmbuild]$

[rpmbuild@rh300vm rpmbuild]$ rpm -ql -p ./RPMS/i686/testrepo-0.0.1-1.el6.i686.rpm
/etc/pki/rpm-gpg/test-gpg-key
/etc/yum.repos.d/test.repo
[rpmbuild@rh300vm rpmbuild]$

[rpmbuild@rh300vm rpmbuild]$ rpm -qp ./RPMS/i686/testrepo-0.0.1-1.el6.i686.rpm --scripts
preinstall scriptlet (using /bin/sh):
echo "Commands to run before package installed"
exit 0
postinstall scriptlet (using /bin/sh):
echo "Commands to run after the package is installed"
exit 0
preuninstall scriptlet (using /bin/sh):
echo "Commmands to run before uninstalling the package"
exit 0
postuninstall scriptlet (using /bin/sh):
echo "Commands to run after uninstalling the package"
exit 0
[rpmbuild@rh300vm rpmbuild]$

[root@rh300vm i686]# rpm -Uvh ./testrepo-0.0.1-1.el6.i686.rpm
Preparing...                ########################################### [100%]
Commands to run before package installed
   1:testrepo               ########################################### [100%]
Commands to run after the package is installed
[root@rh300vm i686]#

[root@rh300vm i686]# rpm -qa --last | head -1
testrepo-0.0.1-1.el6                          Fri 05 Dec 2014 08:08:42 PM GMT
[root@rh300vm i686]#

[root@rh300vm i686]# rpm -e testrepo-0.0.1-1.el6
Commmands to run before uninstalling the package
Commands to run after uninstalling the package
[root@rh300vm i686]# rpm -qa --last | head -1
rpmdevtools-7.5-1.el6                         Fri 05 Dec 2014 07:38:04 PM GMT
[root@rh300vm i686]#

.
|-- BUILD
|   `-- testrepo-0.0.1
|       |-- debugfiles.list
|       |-- debuglinks.list
|       |-- debugsources.list
|       |-- test-gpg-key
|       `-- test.repo
|-- BUILDROOT
|-- README.md
|-- RPMS
|   `-- i686
|       |-- testrepo-0.0.1-1.el6.i686.rpm
|       `-- testrepo-debuginfo-0.0.1-1.el6.i686.rpm
|-- SOURCES
|   |-- testrepo-0.0.1
|   |   |-- test-gpg-key
|   |   `-- test.repo
|   `-- testrepo-0.0.1.tar.gz
|-- SPECS
|   `-- testrepo-0.0.1.spec
`-- SRPMS
    `-- testrepo-0.0.1-1.el6.src.rpm

9 directories, 13 files
```
