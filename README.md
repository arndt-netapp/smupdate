This sample code updates and shows snapmirror relationships.

```
Requirements:
-Python3
-The NMSDKpy library files for Python, in the same directory as this script.

Example of a RBAC role limiting access to a SVM and volume wildcard:

security login role create -role smupdate_role -cmddirname "snapmirror show" -query "-destination-path svlngen4-c01-nas-svl:arndt*" -access all
security login role create -role smupdate_role -cmddirname "snapmirror update" -query "-destination-path svlngen4-c01-nas-svl:arndt*" -access all
security login role create -role smupdate_role -cmddirname version -access readonly
security login create -user-or-group-name smupdate_user -application http -authentication-method password -role smupdate_role
```

Usage:

```
usage: smupdate.py [-h] -o {show,update} -c CLUSTER -u USER [-p PASSWORD] -s
                   SVM -v VOL [-d]

SnapMirror Update Example

optional arguments:
  -h, --help            show this help message and exit
  -o {show,update}, --operation {show,update}
                        Operation type
  -c CLUSTER, --cluster CLUSTER
                        Cluster hostname
  -u USER, --user USER  Username
  -p PASSWORD, --password PASSWORD
                        Password
  -s SVM, --svm SVM     Destination SVM name
  -v VOL, --vol VOL     Destination volume name
  -d, --debug           Enable debug mode
```

