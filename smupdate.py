#!/usr/bin/env python3

# smupdate.py 2023-10-26 version 1.0
# Mike Arndt arndt@netapp.com
#
# This sample code updates and shows snapmirror relationships.
#
# Requirements:
# -Python3
# -The NMSDKpy library files for Python, in the same directory as this script.
#
# Example of a RBAC role limiting access to a SVM and volume wildcard:
#
# security login role create -role smupdate_role -cmddirname "snapmirror show" -query "-destination-path svlngen4-c01-nas-svl:arndt*" -access all
# security login role create -role smupdate_role -cmddirname "snapmirror update" -query "-destination-path svlngen4-c01-nas-svl:arndt*" -access all
# security login role create -role smupdate_role -cmddirname version -access readonly
# security login create -user-or-group-name smupdate_user -application http -authentication-method password -role smupdate_role
#
# THIS SOFTWARE IS PROVIDED BY NETAPP "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN
# NO EVENT SHALL NETAPP BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Version 1.0 - Initial release.

import argparse
import sys
import getpass
sys.path.append("NMSDKpy")
from NaServer import *

# Relax SSL certificate checking.
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

# Function that will connect to ONTAP API.
def NaConnect(cluster,username,password):

    s = NaServer(cluster, 1, 170)
    s.set_server_type('FILER')

    # set communication style - typically just 'LOGIN'
    resp = s.set_style('LOGIN')
    if (resp and resp.results_errno() != 0) :
        r = resp.results_reason()
        print(f"Failed to set authentication style: {r}")
        sys.exit (2)

    # set API transport type - HTTP is the default
    resp = s.set_transport_type('HTTPS')
    if (resp and resp.results_errno() != 0) :
         r = resp.results_reason()
         print(f"Unable to set transport: {r}")
         sys.exit(2)

    # set communication port
    s.set_port(443)

    # Connect and verify
    s.set_admin_user(username, password)
    api = NaElement("system-get-version")
    output = s.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print(f"Error connecting: {r}")
        sys.exit(2)
    else:
        ontap_version = output.child_get_string("version")
        if DEBUG: print(f"Cluster {cluster} is running {ontap_version}")

    # return storage object
    return s

# Function to find a snapmirror relationship
def snapmirror_get(na,dst):
    if DEBUG: print("In snapmirror_get function.")
    # Retrieve the SnapMirror relationship
    api = NaElement("snapmirror-get-iter")
    desired_attributes = NaElement("desired-attributes")
    api.child_add(desired_attributes)
    sm_info = NaElement("snapmirror-info")
    desired_attributes.child_add(sm_info)
    sm_info.child_add_string("source-location", "")
    sm_info.child_add_string("destination-location", "")
    sm_info.child_add_string("relationship-status", "")
    sm_info.child_add_string("mirror-state", "")
    sm_info.child_add_string("lag-time", "")
    query = NaElement("query")
    api.child_add(query)
    sm_info_query = NaElement("snapmirror-info")
    query.child_add(sm_info_query)
    sm_info_query.child_add_string("destination-location", dst)
    output = na.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print(f"Failed snapmirror-get-iter API call: {r}")
    smlist = output.child_get("attributes-list")
    if not smlist:
        print("No snapmirror relationship found.")
        return 1
    print("Source,Destination,State,Status,Lag(Seconds)")
    for sm in smlist.children_get():
        src    = sm.child_get_string("source-location")
        dst    = sm.child_get_string("destination-location")
        status = sm.child_get_string("relationship-status")
        state  = sm.child_get_string("mirror-state")
        lag = sm.child_get_string("lag-time")
        print(f"{src},{dst},{state},{status},{lag}")
    return 1

# Function to update a snapmirror relationship
def snapmirror_update(na,dst):
    if DEBUG: print("In snapmirror_update function.")
    api = NaElement("snapmirror-update") 
    api.child_add_string("destination-location", dst)
    output = na.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print(f"Failed to run snapmirror-create API call: {r}")
    else:
        if DEBUG: print("Success running snapmirror-update.")
    return 1

# Parse the CLI
parser = argparse.ArgumentParser(description='SnapMirror Update Example')
op_values = ['show', 'update']
parser.add_argument('-o', '--operation', type=str, required=True, choices=op_values, help='Operation type')
parser.add_argument('-c', '--cluster', type=str, required=True, help='Cluster hostname')
parser.add_argument('-u', '--user', type=str, required=True, help='Username')
parser.add_argument('-p', '--password', type=str, help='Password')
parser.add_argument('-s', '--svm', type=str, required=True, help='Destination SVM name')
parser.add_argument('-v', '--vol', type=str, required=True, help='Destination volume name')
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
args = parser.parse_args()

# Set debugging values
if args.debug: 
    DEBUG = 1
else:
    DEBUG = 0

# Get cluster password
if args.password:
    password = args.password
else:
    temp = sys.stdout
    sys.stdout = sys.stderr
    passwords_input = getpass.getpass("Enter password: ")
    sys.stdout = temp
    password = passwords_input

# Connect to cluster API
na = NaConnect(args.cluster,args.user,password)

# Perform the requested operation
dst = args.svm + ":" + args.vol
if args.operation == "show":
    snapmirror_get(na,dst)
elif args.operation == "update":
    snapmirror_update(na,dst)
    snapmirror_get(na,dst)
else:
    print("Invalid operation choice.")
