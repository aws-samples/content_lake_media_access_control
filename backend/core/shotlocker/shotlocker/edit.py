# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
from . import s3_utils
from . import stepfn
from . import token
from .cwprint import cwprint, cwprint_exc
import boto3
from botocore.exceptions import ClientError


def get_shot_locker_bucket_edit_list(bucket_name, *, s3_client=None):
    """
    get a list of edits for a given shotlocker
    """
    objects = s3_utils.list_all_prefixes(bucket_name, 'ShotLocker/Edits/', s3_client=s3_client)
    return [o.split('/')[2] for o in objects]


def get_shot_locker_bucket_edit_detailed_list(
    bucket_name, 
    *, 
    s3_client=None, 
    include_inactive=False
):
    """
    get a list of edits with detailed information for a given shotlocker
    """
    if not s3_client:
        s3_client = boto3.client('s3')

    objects = s3_utils.list_all_objects(bucket_name, 'ShotLocker/Edits/', s3_client=s3_client, recursive=True, names_only=False)

    enabled_tag_values = s3_utils.get_enabled_tag_value_list()

    edits = {} 

    for o in objects:

        parts = o['Key'].split('/')

        if len(parts) == 4 or len(parts) == 5:
            # filename parts:
            #   length 4: ShotLocker/Edits/[ACCESS_KEY]/[UPLOADED]
            #   length 5: ShotLocker/Edits/[ACCESS_KEY]/processed/[RESULTS]

            processed = len(parts) == 5

            access_token = parts[2]
            if access_token not in edits:
                edits[access_token] = {
                    'name': access_token,
                    'create_time': None,
                    'original': None,
                    'manifest': None,
                    'results': None,
                    'active': False,
                }

            if processed:
                if parts[-1].endswith('.otio'):
                   edits[access_token]['manifest'] = parts[-1]
                elif parts[-1].endswith('.json'):
                   edits[access_token]['results'] = parts[-1]
            elif (parts[-1].endswith('.xml') or 
                parts[-1].endswith('.aaf') or
                parts[-1].endswith('.otio')):

                edits[access_token]['original'] = parts[-1]
                edits[access_token]['create_time'] = o['LastModified'].isoformat()

                # check if edit is active
                # active is set on the uploaded edit
                try:
                    tag_set = s3_client.get_object_tagging(Bucket=bucket_name, Key=o['Key'])['TagSet']
                except:
                    cwprint_exc(f'get_shot_locker_bucket_edit_detailed_list: get_object_tagging from bucket {bucket_name} key {o["Key"]}')
                    raise

                for tag in tag_set:
                    if tag['Key'] == 'ShotLocker':
                        edits[access_token]['active'] = tag['Value'] in enabled_tag_values


    if not include_inactive:
        active_edits = {}
        for k,v in edits.items():
            if v['active']:
                active_edits[k] = v
        edits = active_edits

    return list(edits.values())


def set_shot_locker_bucket_edit(
    bucket_name, 
    edit_name, 
    *, 
    enable=True, 
    s3_client=None,
    start_stepfn_execution=True
) -> bool:
    """
    Set an S3 Bucket Edit as a Shot Locker bucket enabled or disabled
    @return success
    """
    success = False

    if not s3_client:
        s3_client = boto3.client('s3')

    edit_info = get_shot_locker_bucket_edit_info(bucket_name, edit_name, s3_client=s3_client, as_s3_uri=False)

    # use the original upload as the source of enabled or not
    key = edit_info['original']
    if not key:
        return False

    # ShotLocker tag
    tag_enable = 'true' if enable else 'false'

    tag_set = []
    try:
        tag_set = s3_client.get_object_tagging(Bucket=bucket_name, Key=key)['TagSet']
    except:
        cwprint_exc(f'set_shot_locker_bucket_edit: get_object_tagging from bucket {bucket_name} key {key}')
        return False

    enabled_tag_values = s3_utils.get_enabled_tag_value_list()

    changed = False
    found = False
    for tag in tag_set:
        if 'Key' in tag and tag['Key'] == 'ShotLocker':
            found = True
            current = tag['Value'] in enabled_tag_values
            if current != tag_enable:
                tag['Value'] = tag_enable
                changed = True

    if not found:
        tag_set.append({'Key': 'ShotLocker', 'Value': tag_enable})
        changed = True

    # if not changed the shotlocker enablement, no need for updates
    if not changed:
        return success

    try:
        cwprint({'TagSet': tag_set})
        s3_client.put_object_tagging(Bucket=bucket_name, Key=key, Tagging={'TagSet': tag_set})
        success = True
    except:
        cwprint_exc(f'set_shot_locker_bucket_edit: put_object_tagging to bucket {bucket_name} key {key}')

    if start_stepfn_execution:
        # call step function to complete edit activation
        edit_stepfn = "AddEditAccessArn" if enable else "RemoveEditAccessArn"
        edit_mode = "add" if enable else "remove"
        stepfn_name = stepfn.get_stepfn_arn(edit_name, edit_stepfn)

        try:
            sfn_client = boto3.client('stepfunctions')
            response = sfn_client.start_execution(
                stateMachineArn=stepfn_name,
                input=json.dumps({
                    'bucket': bucket_name,
                    'edit_id': edit_name,
                    'key': edit_info['manifest'],
                    'mode': edit_mode
                }),
                traceHeader=edit_stepfn
            )
        except Exception as e:
            cwprint_exc()
            success = False

    return success


def is_shot_locker_bucket_edit_valid(bucket_name, edit_name, *, s3_client=None):
    edits = get_shot_locker_bucket_edit_list(bucket_name, s3_client=s3_client)
    return edit_name in edits


def get_shot_locker_bucket_edit_info(bucket_name, edit_name, *, s3_client=None, as_s3_uri=True):
    edit = {
        'name': edit_name,
        "original": None,
        "create_time": None,
        "manifest": None,
        "results": None,
        "process_status": None,
        "active": True
    }

    if not s3_client:
        s3_client = boto3.client('s3')

    edits = get_shot_locker_bucket_edit_list(bucket_name, s3_client=s3_client)
    if edit_name not in edits:
        return None

    objects = s3_utils.list_all_objects(bucket_name, f'ShotLocker/Edits/{edit_name}/', s3_client=s3_client, names_only=False, recursive=True)

    original_upload_name = None

    for o in objects:
        name = o['Key']

        processed = '/processed/' in name

        if processed:
            if name.endswith('.otio'):
                edit['manifest'] = f's3://{bucket_name}/{name}' if as_s3_uri else name
            elif name.endswith('.json'):
                edit['results'] = f's3://{bucket_name}/{name}' if as_s3_uri else name
        elif (name.endswith('.xml') or 
              name.endswith('.aaf') or
              name.endswith('.otio')):
            edit['original'] = f's3://{bucket_name}/{name}' if as_s3_uri else name
            edit['create_time'] = o['LastModified'].isoformat()
            original_upload_name = name

    # check if edit is active
    # if the ShotLocker tag is missing, assume it is active
    if not original_upload_name:
        raise IOError(f"Unable to find original upload for {edit_name}")
    try:
        tag_set = s3_client.get_object_tagging(Bucket=bucket_name, Key=original_upload_name)['TagSet']
    except:
        cwprint_exc(f'get_shot_locker_bucket_edit_info: get_object_tagging from bucket {bucket_name} key {name}')
        raise

    enabled_tag_values = s3_utils.get_enabled_tag_value_list()
    for tag in tag_set:
        if tag['Key'] == 'ShotLocker':
            edit['active'] = tag['Value'] in enabled_tag_values

    # Get the process status
    # AWS Account Id
    account_id = boto3.client('sts').get_caller_identity()["Account"]

    aws_partition = os.environ.get('AWS_PARTITION')
    aws_region = os.environ.get('AWS_REGION')
    arn = f'arn:{aws_partition}:states:{aws_region}:{account_id}:execution:ShotLocker-Process-Edit-StepFn:ShotLocker-Put-Object-StepFn-{edit_name}'
    try:
        sf_client = boto3.client('stepfunctions')
        resp = sf_client.describe_execution(executionArn=arn)
        edit['process_status'] = resp['status']
    except:
        cwprint_exc(f"ERROR: Unable to retrieve the stepfunction execution (arn {arn})")

    return edit


def create_new_edit_folder(bucket_name, *, s3_client=None):
    if not s3_client:
        s3_client = boto3.client('s3')

    current_edits = get_shot_locker_bucket_edit_list(bucket_name, s3_client=s3_client)

    found = False
    while not found:
        access_token = token.create_access_token()
        if access_token in current_edits:
            continue
        test_key = f'ShotLocker/Edits/{access_token}/'

        try:
            s3_client.head_object(Bucket=bucket_name, Key=test_key)
        except ClientError:
            found = True

        if found:
            try:
                s3_client.put_object(Bucket=bucket_name, Body='', Key=test_key)
            except ClientError:
                found = False

    return test_key


def upload_new_edit(bucket_name, filename, body, *, s3_client=None):
    
    if not s3_client:
        s3_client = boto3.client('s3')

    folder = create_new_edit_folder(bucket_name, s3_client=s3_client)
    if not folder:
        return None

    key = folder + filename

    try:
        s3_client.put_object(Bucket=bucket_name, Body=body, Key=key)
    except ClientError:
        return None

    return key

