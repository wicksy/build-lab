<%#
kind: snippet
name: proxy.sh
%>

export http_proxy=http://proxy:8080
export ftp_proxy=http://proxy:8080
export https_proxy=http://proxy:8080
export HTTP_PROXY=http://proxy:8080
export FTP_PROXY=http://proxy:8080
export no_proxy=localhost,127.0.0.1
export EC2_JVM_ARGS="-Dhttps.proxyHost=proxy -Dhttps.proxyPort=8080"
