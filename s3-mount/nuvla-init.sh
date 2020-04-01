#!/bin/bash

#
# generate a random access token
#

token=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 15 | head -n 1`
echo "generated access token: ${token}"
echo -n ${token} > /home/jovyan/token.txt

#
# run Nuvla integration
#

/usr/local/bin/nuvla-integration.py
rm -rf /home/jovyan/token.txt /home/jovyan/.nuvla/

#
# Mount data if any.
#
sudo -E -H -u jovyan /opt/conda/bin/python3 /usr/local/bin/nuvla-data-mount.py

#
# force use of SSL with generated certificate
#

export GEN_CERT=yes

#
# start notebook
#

/usr/local/bin/start-notebook.sh --NotebookApp.token=${token} --allow-root
