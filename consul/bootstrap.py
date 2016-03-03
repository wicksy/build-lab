#!/usr/bin/env python

# Sample bootstrap for VMs picking up bootstrap metadata from Consul. Tested on Centos and pfSense (FreeBSD)
#

# Imports
import base64
import httplib
import json
import os
import re
import socket
import subprocess
import sys
import syslog
import yaml

# Function: Clean up and Exit
def die(CODE):
  try:
      FILE.close()
  except:
    pass

  syslog.syslog(syslog.LOG_ERR, "Exit with code " + str(CODE))
  sys.exit(CODE)

# Function: Make a directory if not exist
def ensure_dir(MKDIR):
  DIR = os.path.dirname(MKDIR)
  if not os.path.exists(DIR):
    try:
      os.makedirs(DIR)
    except:
      syslog.syslog(syslog.LOG_ERR, "Error making directory " + str(MKDIR))
      die(EXIT_MKDIR)

# Exit codes
EXIT_MKDIR = 110
EXIT_LIST_INTERFACES_FAIL = 120
EXIT_SOCKET_CONNECT = 130
EXIT_KV_GET_FAIL = 140
EXIT_JSON_LOAD_ERROR = 150
EXIT_YAML_EXCEPTION = 160
EXIT_NO_KEYSTORE_DATA = 170
EXIT_YAML_VARS = 180
EXIT_YAML_SCRIPT = 190
EXIT_VARS_WRITE = 200
EXIT_SCRIPT_WRITE = 210
EXIT_CUSTOM_SCRIPT_FAIL = 220

# Which OS?
ISLINUX = False
ISFREEBSD = False
PLATFORM = os.uname()[0].lower()

# OS specifics
if PLATFORM == "linux":
  ISLINUX = True
  IP = str("/usr/sbin/ip link show").split()
if PLATFORM == "freebsd":
  ISFREEBSD = True
  IP = str("/sbin/ifconfig").split()

# Generic Vars
MACS = []
KEYSTORE_HOST = "keystore"
KEYSTORE_PORT = 8500
KVPATH = "/v1/kv"
CUSTOM_DIR = "/usr/local/bin"
CUSTOM_SCRIPT = CUSTOM_DIR + "/" + "customisation.sh"
CUSTOM_VARS = CUSTOM_DIR + "/" +"customisation_vars.sh"

# Main
syslog.syslog(syslog.LOG_NOTICE, "Bootstrap starting")

# Which platform? If VirtualBox end here. Otherwise boot on MacDuff.
if ISLINUX:
  DMI_CMD = "/sbin/dmidecode -s system-product-name"
if ISFREEBSD:
  DMI_CMD = "/usr/local/sbin/dmidecode -s system-product-name"

try:
  PLATFORM = os.popen(DMI_CMD).read().strip('\n').lower()
except:
  PLATFORM = ""

if PLATFORM == "virtualbox":
  syslog.syslog(syslog.LOG_NOTICE, "Running on Virtualbox so ending here")
  die(0)

# Get IP link info
try:
  IP_PROCESS = subprocess.Popen(IP, stdout=subprocess.PIPE)
  IP_PROCESS.wait()
except:
  die(EXIT_LIST_INTERFACES_FAIL)

# Failed to get ip link info
if IP_PROCESS.returncode != 0:
  syslog.syslog(syslog.LOG_ERR, "Error " + str(IP_PROCESS.returncode) + " from " + str(' '.join(IP)))
  die(EXIT_LIST_INTERFACES_FAIL)

# Find interface names and MACs
for LINE in IP_PROCESS.stdout:

  if ISLINUX:
    if re.match('^[0-9]+:.*: <', LINE):
      DHCP_INTERFACE = LINE.split()
  if re.match('.*link\/ether.*', LINE):
     MACS.append(LINE.split()[1])

  if ISFREEBSD:
    if re.match('^[a-zA-Z]+.*[0-9]+:.*BROADCAST.*', LINE):
      DHCP_INTERFACE = LINE.split()
    if re.match('.*ether [0-9a-f][0-9a-f].*', LINE):
      MACS.append(LINE.split()[1])

# DHCP the last interface
if DHCP_INTERFACE:
  if ISLINUX:
    DEVID = str(DHCP_INTERFACE[1]).strip(':')
  if ISFREEBSD:
    DEVID = str(DHCP_INTERFACE[0]).strip(':')

  syslog.syslog(syslog.LOG_NOTICE, "Starting dhclient for interface " + DEVID)

  if ISLINUX:
    DHCLIENT = str("/usr/sbin/dhclient " + DEVID).split()
  if ISFREEBSD:
    DHCLIENT = str("/sbin/dhclient -b " + DEVID).split()

# We don't bother checking exit codes here from dhclient as it might already be started. Just rely on the
# Key Store connection failing as being the point at which we report a problem if there is one with DHCP
  try:
    DH_PROCESS = subprocess.Popen(DHCLIENT, stdout=subprocess.PIPE)
    DH_PROCESS.wait()
  except:
    pass

# If this is FreeBSD then generate resolv.conf using pfSsh playbook
if ISFREEBSD:
  syslog.syslog(syslog.LOG_NOTICE, "Regenerating resolv.conf")
  os.system("/usr/local/sbin/pfSsh.php playback regen_resolv")

# Test connection to Key Store
try:
  sock = socket.create_connection((KEYSTORE_HOST, KEYSTORE_PORT), timeout=60)
except:
  syslog.syslog(syslog.LOG_ERR, "Error connecting to " + KEYSTORE_HOST + ":" + str(KEYSTORE_PORT))
  die(EXIT_SOCKET_CONNECT)

# Find my Key Store boot info (keyed on MAC address)
DATA = False
for MAC in MACS:

  URL = str(KVPATH + "/" + str(MAC) + "/booty").strip()

  try:
    KV = httplib.HTTPConnection(host=KEYSTORE_HOST, port=KEYSTORE_PORT, timeout=10)
  except:
    die(EXIT_KV_GET_FAIL)

  try:
    KV.request("GET", URL)
  except:
    continue

  try:
    RESPONSE = KV.getresponse()
  except:
    continue

  if RESPONSE:
    if RESPONSE.status == 200 and RESPONSE.reason == "OK":
      syslog.syslog(syslog.LOG_NOTICE, "Found keystore boot info for interface " + MAC)
      DATA = RESPONSE.read()

# Found Key Store data
if DATA:

# Strip off leading [ and trailing ] and read remainder as JSON
  DATA = DATA[1:len(DATA) - 1]
  try:
    JSON = json.loads(DATA)
  except:
   die(EXIT_JSON_LOAD_ERROR)

# Decode Value (stored as encoded base64)
  BOOTY64 = JSON["Value"]
  YAML = base64.b64decode(str(BOOTY64))

# Value should now be my boot info (in YAML format)
  try:
    BOOTY = yaml.safe_load(YAML)
  except yaml.YAMLError as YAML_EXCEPTION:
    syslog.syslog(syslog.LOG_ERR, str(YAML_EXCEPTION))
    die(EXIT_YAML_EXCEPTION)

# Make target directory for stage two scripts (customisation)
  ensure_dir(CUSTOM_DIR)

# Write customisation variables out to vars script
  VARS = ""
  try:
    for VAR in BOOTY['customisation']['vars']:
      OUTPUT = "export " + VAR.upper() + "=" + '"' + str(BOOTY['customisation']['vars'][VAR]) + '"' + "\n"
      VARS += OUTPUT
  except:
    syslog.syslog(syslog.LOG_ERR, "Error locating customisation variables")
    die(EXIT_YAML_VARS)

  try:
    with open(CUSTOM_VARS, 'w') as FILE:
      FILE.write(VARS)
      os.chmod(CUSTOM_VARS, 0700)
  except:
    syslog.syslog(syslog.LOG_ERR, "Error writing to " + CUSTOM_VARS)
    die(EXIT_VARS_WRITE)

  FILE.close()

# Write customisation script out to customisation script
  CUSTOM = ""
  try:
    for SCRIPT in BOOTY['customisation']['script']:
      CUSTOM += SCRIPT
  except:
    syslog.syslog(syslog.LOG_ERR, "Error locating customisation script")
    die(EXIT_YAML_SCRIPT)

  try:
    with open(CUSTOM_SCRIPT, 'w') as FILE:
      FILE.write(CUSTOM)
      os.chmod(CUSTOM_SCRIPT, 0700)
  except:
    syslog.syslog(syslog.LOG_ERR, "Error writing to " + CUSTOM_SCRIPT)
    die(EXIT_SCRIPT_WRITE)

  FILE.close()

# Go stage 2 bootstrap (customisation script)
  syslog.syslog(syslog.LOG_NOTICE, "Starting customisation script " + CUSTOM_SCRIPT)
  try:
    CS_PROCESS = subprocess.Popen(CUSTOM_SCRIPT, stdout=subprocess.PIPE)
    CS_PROCESS.wait()
  except:
    syslog.syslog(syslog.LOG_ERR, "Error calling script " + CUSTOM_SCRIPT)
    die(EXIT_CUSTOM_SCRIPT_FAIL)

  for LINE in CS_PROCESS.stdout:
    syslog.syslog(syslog.LOG_NOTICE, LINE)

# Customisation script failure
  if CS_PROCESS.returncode != 0:
    syslog.syslog(syslog.LOG_ERR, "Error " + str(CS_PROCESS.returncode) + " from " + CUSTOM_SCRIPT)
    die(EXIT_CUSTOM_SCRIPT_FAIL)

# Customisation must have worked if we got here so kill dhclient off and prep the interface for
# teardown by the provisioner
  if ISLINUX:
    DH_PROCESS = str(' '.join(DHCLIENT))
    DH_KILL_STR = "'" + DH_PROCESS + "'"

  if ISFREEBSD:
    DH_PROCESS = "dhclient.* " + DEVID
    DH_KILL_STR = "'" + DH_PROCESS + "'"

  syslog.syslog(syslog.LOG_NOTICE, "Killing off " + DH_KILL_STR)
  os.system("/bin/pkill -f " + DH_KILL_STR)

# Down interface
  syslog.syslog(syslog.LOG_NOTICE, "Downing interface " + DEVID)
  if ISLINUX:
    IF = str("/sbin/ifdown " + DEVID)
  if ISFREEBSD:
    IF = str("/sbin/ifconfig " + DEVID + " down")

  os.system(IF)

# Remove config file for interface (Linux only)
  if ISLINUX:
    CFG = "/etc/sysconfig/network-scripts/ifcfg-" + DEVID
    syslog.syslog(syslog.LOG_NOTICE, "Removing " + CFG)
    os.system("/bin/rm -f " + CFG)

# No Key Store data found for any of my MACs
else:
    syslog.syslog(syslog.LOG_ERR, "No keystore information found for any interface")
    die(EXIT_NO_KEYSTORE_DATA)

# Fin
die(0)
