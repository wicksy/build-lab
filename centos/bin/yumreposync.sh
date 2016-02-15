#!/bin/bash
#
# Sync a remote repository to a local directory.
#
# If the script sees a local directory with nothing in it, it is assumed that this is the first time it has been run via
# a Salt "highstate" so it runs a sync. Because the script is part of a "cmd.run" state in Salt, subsequent runs will not
# sync (because the local directory now has content). This is to avoid a full sync (as wget has no concept of incremental
# updates or rsync capabilities) every time a "highstate" is run (which could be regularly via Minion schedules).
#
# To allow for a regular (e.g. nightly) refresh of a repo, a --forcesync option is included. If the local directory is
# empty a sync will be run (as it is assumed this is the first run on the first "highstate") so in this instance
# --forcesync has no effect.
#
# See usage() for details on how to call this script
#

# Ensure any failed commands within a pipeline result in an appropriate exit code from the entire pipeline
set -o pipefail

## Variable Declartions ##

# Who am I
SCRIPTNAME=$(echo "$(/bin/basename ${0})")

# Log file
LOGFILE="/tmp/${SCRIPTNAME}.log"
/bin/rm -f "${LOGFILE}"

# Function: Tell me how to use this script
usage() {
  echo "Usage: ${SCRIPTNAME} -l|--local local_path -r|--repoid repo_id -m|--mailto recipient,recipient...,recipient [ -d|--repodata repodata_location] [-g|--gpgkey gpgkey_location] [-c|--createrepo True|False] [-f|--forcesync True|False] [-h|--help]"
  echo ""
  echo "MANDATORY:"
  echo "local:      Path to local repository"
  echo "repoid:     Remote repository to sync with local (the name in the /etc/yum.repos.d/ repo file)"
  echo "mailto:     List of comma delimited mail addresses to send report to (no whitespace allowed)"
  echo ""
  echo "OPTIONAL:"
  echo "repodata:   Remote location of repo metadata to download (default is to not download)"
  echo "gpgkey:     Remote location of gpg key to download (default is to not download)"
  echo "createrepo: Run createrepo(8) after repo sync (default is False)"
  echo "forcesync:  Run a sync regardless of whether the local repository is empty or not (default is False)"
  echo "help:       Display this usage"
  return
}

# Function: Clean up, report and exit
die() {
  EXITCODE="${1}"
  log "Exiting with code ${EXITCODE}"
  mail
  exit "${EXITCODE}"
}

# Function: Log an event
log() {
  LOGMSG="${*}"
  echo "[$(date +"%Y-%m-%d"+"%T")]: (${SCRIPTNAME}) ${LOGMSG}" \
    | /usr/bin/tee -a "${LOGFILE}"
}

# Function: Mail report - only when errors as called by die()
mail() {
  SUBJECT="Yum Repository Sync ($(/bin/date '+%d%m%Y'))"
  log "Mailing report to ${MAILTO}"
  echo "Repository sync failed. See log for details (${LOGFILE})" \
    | /bin/mailx -s "${SUBJECT}" "${MAILTO}"
}

# Function: Sync remote repo rpms to local path
syncrpms() {
  cd "${LOCAL}" && /usr/bin/reposync -r "${REPOID}" --norepopath --plugins --downloadcomps --quiet || die 100
}

# Function: Pull down repodata (repo metadata)
pullrepodata() {
  if [[ "${REPODATA}" ]] ; then
    log "Pulling repodata from ${REPODATA}"
    cd "${LOCAL}/repodata/" && /usr/bin/wget -q -T 180 -t 6 --waitretry 10 -e robots=off -P . -nH -nd -r -np -k "${REPODATA}" || die 105
  fi
}

# Function: Pull down gpg key
pullgpgkey() {
  if [[ "${GPGKEY}" ]] ; then
    log "Pulling GPG key from ${GPGKEY}"
    cd "${LOCAL}" && /usr/bin/wget -q -T 180 -t 6 --waitretry 10 -e robots=off -P . -nH -nd -np -k "${GPGKEY}" || die 110
  fi
}

# Process options and parameters

SHORTOPTS="hl:r:c:f:m:d:g:"
LONGOPTS="help,local:,repoid:,createrepo:,forcesync:,mailto:,repodata:,gpgkey:"

ARGS=$(getopt -s bash --options ${SHORTOPTS} \
  --longoptions ${LONGOPTS} -- "$@")
RC=${?}
if [[ ${RC} -ne 0 ]]; then
  usage
  die 1
fi

eval set -- "${ARGS}"

while true; do
  case ${1} in
    -h|--help)
      usage
      exit 0
      ;;
    -l|--local)
      shift
      LOCAL="${1}"
      ;;
    -r|--repoid)
      shift
      REPOID="${1}"
      ;;
    -c|--createrepo)
      shift
      CREATEREPO="${1}"
      ;;
    -f|--forcesync)
      shift
      FORCESYNC="${1}"
      ;;
    -m|--mailto)
      shift
      MAILTO="${1}"
      ;;
    -d|--repodata)
      shift
      REPODATA="${1}"
      ;;
    -g|--gpgkey)
      shift
      GPGKEY="${1}"
      ;;
    --)
      shift
      break
      ;;
    *)
      shift
      break
      ;;
  esac
  shift
done

# Set some defaults if certain switches not specified
CREATEREPO=${CREATEREPO:-False}
FORCESYNC=${FORCESYNC:-False}

# Make sure we have everything we need
if [[ -z ${LOCAL} ]] ; then
  log "Local path not specified"
  usage
  die 1
elif [[ ! -d ${LOCAL} ]] ; then
  log "${LOCAL} path does not exist"
  usage
  die 1
elif [[ -z ${REPOID} ]] ; then
  log "Remote repo id not specified"
  usage
  die 1
elif [[ ${CREATEREPO} != "True" && ${CREATEREPO} != "False" ]] ; then
  log "Invalid Create Repo mode (should be True or False)"
  usage
  die 1
elif [[ ${FORCESYNC} != "True" && ${FORCESYNC} != "False" ]] ; then
  log "Invalid Force Sync mode (should be True or False)"
  usage
  die 1
elif [[ -z ${MAILTO} ]] ; then
  log "Mail recipients not specified"
  usage
  die 1
fi

# Log some runtime details
log "Local path: ${LOCAL}"
log "Remote repo id: ${REPOID}"
log "Repodata: ${REPODATA:-None}"
log "GPG key: ${GPGKEY:-None}"
log "Run createrepo(8): ${CREATEREPO}"
log "Force sync: ${FORCESYNC}"
log "Mailing to: ${MAILTO}"

# If local directory is empty (no files) do an initial rpm sync (ignore any other options)
if [[ $(/bin/find ${LOCAL} -mount -type f | /usr/bin/wc -l) == 0 ]] ; then
  log "${LOCAL} is empty so initial rpm sync will be run"
  syncrpms
  pullrepodata
  pullgpgkey
else
  log "${LOCAL} is not empty"

  # Do a sync only if --forcesync is True

  if [[ "${FORCESYNC}" == "True" ]] ; then
    log "Forcing an rpm sync"
    syncrpms
    pullrepodata
    pullgpgkey
  else
    log "Not running an rpm sync (not empty)"
  fi
fi

# Should we run createrepo(8) or not?
if [[ "${CREATEREPO}" == "True" ]] ; then
  log "Running a createrepo against the local path"
  cd "${LOCAL}" && /usr/bin/createrepo . || die 120
else
  log "Not running a createrepo"
fi

log "Repository update complete"

exit 0
