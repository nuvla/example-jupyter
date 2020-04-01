#!/usr/bin/env python3

import sys
import time
import os
import uuid
from subprocess import run, PIPE, STDOUT, TimeoutExpired
from nuvla.api import Api


def from_data_uuid(text):
    class NullNameSpace:
        bytes = b''

    return str(uuid.uuid3(NullNameSpace, text))


def deployment_param_href(deployment_id, node_id, param_name):
        param_id = ':'.join(item or '' for item in [deployment_id, node_id, param_name])
        return 'deployment-parameter/' + from_data_uuid(param_id)


def find_s3_creds(nuvla, depl_id):
    # Go up from deployment to infra service (IS) group:
    # deployment -> IS creds -> IS -> IS group
    # Find S3 IS in the group and find IS creds of it:
    # IS group -> S3 IS -> S3 IS creds

    # Deployment
    res = nuvla.get(depl_id)

    # IS creds is the parent of the deployment.
    infra_service_cred_id = res.data['parent']
    res = nuvla.get(infra_service_cred_id)

    # IS is the parent of the IS creds.
    infra_service_id = res.data['parent']
    res = nuvla.get(infra_service_id)

    # IS group is the parent of IS.
    infra_service_group = res.data['parent']
    res = nuvla.get(infra_service_group)

    # Find S3 IS in the group.
    s3_infra_service = None
    for infra_service in map(lambda x: x['href'], res.data['infrastructure-services']):
        res = nuvla.get(infra_service)
        if 's3' == res.data['subtype']:
            s3_infra_service = res.data
            break

    # Get all creds who's parent is S3 IS.
    s3_infra_service_id = s3_infra_service['id']
    _filter = "parent='{}'".format(s3_infra_service_id)
    res = nuvla.search('credential', filter=_filter)
    if res.count < 1:
        raise SystemExit('No creds fround for IS {}'.format(s3_infra_service_id))
    # Grab the first one and extract the creds.
    s3_infra_service_creds = res.data['resources'][0]
    key = s3_infra_service_creds['access-key']
    secret = s3_infra_service_creds['secret-key']
    endpoint = s3_infra_service['endpoint']

    return endpoint, key, secret


def run_command(cmd):
    timeout = 15
    try:
        result = run(cmd, stdout=PIPE, stderr=STDOUT, timeout=timeout,
                     encoding='UTF-8')
    except TimeoutExpired:
        raise Exception('Command execution timed out after {} seconds'.format(timeout))
    if result.returncode == 0:
        return result.stdout
    else:
        raise Exception(result.stdout)

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
  print('Missing required configuration information; skipping data mounts...')
  sys.exit()

#
# setup the Nuvla API
#

api = Api(endpoint=endpoint, insecure=True)
api.login_apikey(api_key, api_secret)

# Recover deployment information.

deployment = api.get(deployment_id)

print('Getting data records...')
records = {}
if 'data' in deployment.data and 'records' in deployment.data['data']:
    data_record_filters = deployment.data['data']['records']['filters']
    print('Filters to process', data_record_filters)
    for drf in data_record_filters:
        dr_filter = drf['filter']
        time_start = drf['time-start']
        time_end = drf['time-end']
        drs_filter_mask = "(timestamp>='{0}' and timestamp<='{1}') and {2}"
        data_records_filter = drs_filter_mask.format(time_start,
                                                     time_end, dr_filter)
        print('Initial data records filter: {}'.format(data_records_filter))
        cycle_count = 1
        ndrs = 0
        last_timestamp = None
        collected_total = 0
        while True:
            t_s = time.time()
            print('::: Page: {}'.format(cycle_count))
            res = api.search('data-record',
                             filter=data_records_filter,
                             select=['bucket', 'object', 'timestamp'],
                             aggregation='value_count:id',
                             orderby='timestamp:asc')
            print('Time to get records: {:.3f} sec'.format(time.time() - t_s))
            if len(res.data['resources']) <= 0:
                print('No more data records to collect.')
                break
            if cycle_count == 1:
                ndrs = res.data['aggregations']['value_count:id']['value']
                print('Number of data records to collect: {}'.format(ndrs))
            for dr in res.data['resources']:
                obj = dr['object']
                bucket = dr['bucket']
                if bucket in records:
                    records[bucket].append(obj)
                else:
                    records[bucket] = [obj]
            collected = len(res.data['resources'])
            collected_total = collected_total + collected
            if collected_total >= ndrs:
                print('All data records collected.')
                break
            print('collected total: {0}, collected now: {1}, left: {2}'\
                  .format(collected_total, collected, ndrs - collected_total))
            last_timestamp = res.data['resources'][-1]['timestamp']
            data_records_filter = drs_filter_mask.format(last_timestamp,
                                                         time_end, dr_filter)
            print('Updated data records filter: {}'.format(data_records_filter))
            cycle_count += 1
else:
    print("No data records provided in deployment.")
    sys.exit(1)

if len(records) == 0:
    print('No data records collected.')
    sys.exit(1)
else:
    collected = 0
    for b in records.keys():
        collected += len(records[b])
    print('Number of collected data records: {}'.format(collected))

print('Getting S3 creds...')
endpoint, key, secret = find_s3_creds(api, deployment_id)
print('- endpoint: %s' % endpoint)
print('- key: %s' % key)
print('- secret: %s..%s' % (secret[:2], secret[-2:]))
passwd_fn = os.path.expanduser('~/.passwd-s3fs')
with open(passwd_fn, 'w') as fh:
    fh.write('%s:%s' % (key, secret))
os.chmod(passwd_fn, 0o600)

print('Mounting buckets ...')
mnt_base = os.path.expanduser('/tmp/mnt')
try:
    os.mkdir(mnt_base)
except FileExistsError:
    pass
for bucket in records.keys():
    mnt_dir = os.path.join(mnt_base, bucket)
    try:
        os.mkdir(mnt_dir)
    except FileExistsError:
        pass
    options = 'url={0},passwd_file={1},uid={2},gid={3},umask={4}' \
        .format(endpoint, passwd_fn, os.getuid(), os.getgid(), '000')
    cmd = ['s3fs', bucket, mnt_dir, '-o', options]
    print('Run command:', cmd)
    run_command(cmd)

dst_base = os.path.expanduser('~/work/data')
os.makedirs(dst_base, exist_ok=True)
file_list = '{}/full-file-path.txt'.format(dst_base)
with open(file_list, 'w') as fh_file_list:
    print('Linking data to %s ...' % dst_base)
    for bucket, objects in records.items():
        src_dir = os.path.join(mnt_base, bucket)
        dst_dir = '%s/%s' % (dst_base, bucket)
        os.makedirs(dst_dir, exist_ok=True)
        for obj in objects:
            src = '{0}/{1}'.format(src_dir, obj)
            dst = '{0}/{1}'.format(dst_dir, obj)
            try:
                os.symlink(src, dst)
            except FileExistsError:
                pass
            except Exception as ex:
                print('Failed to link: %s' % ex)
            fh_file_list.write('{}\n'.format(dst))

print('DONE data mounts ...')
