#!/usr/bin/env python

import sys
import os
import uuid
from nuvla.api import Api
import docker

#
# constants and utility functions
#

deployment_params_filter="deployment/href='{}' and name='{}'"

def from_data_uuid(text):
    class NullNameSpace:
        bytes = b''

    return str(uuid.uuid3(NullNameSpace, text))

def deployment_param_href(deployment_id, node_id, param_name):
        param_id = ':'.join(item or '' for item in [deployment_id, node_id, param_name])
        return 'deployment-parameter/' + from_data_uuid(param_id)

#
# Read the configuration from the environment.
#

endpoint = os.getenv('NUVLA_ENDPOINT')
api_key = os.getenv('NUVLA_API_KEY')
api_secret = os.getenv('NUVLA_API_SECRET')
deployment_id = os.getenv('NUVLA_DEPLOYMENT_ID')

#
# Ensure complete environment or bail out.
#

if (endpoint is None or
    api_key is None or
    api_secret is None or
    deployment_id is None):
  print("missing required configuration information; skipping nuvla integration...")
  sys.exit()

#
# setup the Nuvla API
#

api = Api(endpoint=endpoint, insecure=True)
api.login_apikey(api_key, api_secret)

# Recover deployment information.

deployment = api.get(deployment_id)

#
# recover the access token
#

token = None
with open('/home/jovyan/token.txt', 'r') as f:
  token = f.read()

#
# write value to Nuvla deployment parameter
#

param_id = deployment_param_href(deployment_id, None, 'access-token')

if token is not None:
    print("Publish token...")
    api.edit(param_id, {'value': token})
 
#
# Discover and set my real hostname.
#

if 'NODE_IP' in os.environ:
    param_id = deployment_param_href(deployment_id, None, 'hostname')
    api.edit(param_id, {'value': os.environ['NODE_IP']})

#
# Discover and set my real port.
#

client = docker.from_env()
for container in client.containers.list():
    if container.name == os.environ['CONT_NAME']:
        ports = container.ports.get('8888/tcp', [])
        if len(ports) > 0:
            param_id = deployment_param_href(deployment_id, None, 'public-port')
            port = ports[0]['HostPort']
            print("Publish port: %s" % port)
            api.edit(param_id, {'value': port})
