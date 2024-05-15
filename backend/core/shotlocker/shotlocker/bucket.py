# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
from .cwprint import cwprint, cwprint_exc
from . import s3_utils
from . import stepfn
import boto3
from botocore.exceptions import ClientError


def get_shot_locker_bucket_list(*, s3_client=None, include_inactive=True):
    """
    @returns list of shotlocker buckets
    """
    sl_buckets = []

    if not s3_client:
        s3_client = boto3.client('s3')
    
    buckets = s3_client.list_buckets()['Buckets']

    enabled_tag_values = s3_utils.get_enabled_tag_value_list()

    # list all of the buckets with ShotLocker tag
    for bucket in buckets:
        bucket_name = bucket['Name']
        try:
            tag_set = s3_client.get_bucket_tagging(Bucket=bucket_name)['TagSet']
        except:
            tag_set = []

        for tag in tag_set:
            if tag['Key'] == 'ShotLocker':
                if include_inactive or (not include_inactive and tag['Value'] in enabled_tag_values):
                    sl_buckets.append({
                        'name': bucket_name, 
                        'tags': tag_set,
                        'active': tag['Value'] in enabled_tag_values
                    })

    return sl_buckets


def get_shot_locker_available_bucket_list(*, s3_client=None):
    """
    @returns list of buckets available to be used for Shot Locker
    """
    avail_buckets = []

    if not s3_client:
        s3_client = boto3.client('s3')
    
    buckets = s3_client.list_buckets()['Buckets']

    enabled_tag_values = s3_utils.get_enabled_tag_value_list()

    # skip buckets with a starting name prefix
    skip_prefix = ('cloudtrail-', 
                   'sagemaker-', 
                   'kendra-', 
                   'do-not-delete-', 
                   'cf-templates-', 
                   'aws-', 
                   'amplify-', 
                   'cdk-', 
                   'cloudfront', 
                   'shotlocker-stack-')

    # list all of the buckets with ShotLocker tag
    for bucket in buckets:
        bucket_name = bucket['Name']

        if bucket_name.startswith(skip_prefix):
            continue

        is_shot_locker_bucket = False
        tag_set = []
        try:
            # if there are no tagsets set on the bucket, will throw exception
            tag_set = s3_client.get_bucket_tagging(Bucket=bucket_name)['TagSet']
            for tag in tag_set:
                if tag['Key'] == 'ShotLocker' and tag['Value'] in enabled_tag_values:
                    is_shot_locker_bucket = True
            
        except ClientError as e:
            pass

        if not is_shot_locker_bucket:
            avail_buckets.append({
                'name': bucket_name, 
                'tags': tag_set,
                'active': False,
            })

    return avail_buckets


def set_shot_locker_bucket(
    bucket_name, 
    *, 
    enable=True, 
    s3_client=None,
    start_stepfn_execution=True
) -> bool:
    """
    Set an S3 Bucket as a Shot Locker bucket enabled or disabled
    @return success
    """
    success = False

    if not s3_client:
        s3_client = boto3.client('s3')

    # notify event lambda
    if enable:
        _add_bucket_upload_notification(bucket_name, s3_client=s3_client)
    else:
        _remove_bucket_upload_notification(bucket_name, s3_client=s3_client)

    # ShotLocker tag
    tag_enable = 'true' if enable else 'false'

    try:
        tag_set = s3_client.get_bucket_tagging(Bucket=bucket_name)['TagSet']
    except ClientError as e:
        tag_set = []

    found = False
    for tag in tag_set:
        if 'Key' in tag and tag['Key'] == 'ShotLocker':
            tag['Value'] = tag_enable
            found = True

    if not found:
        tag_set.append({'Key': 'ShotLocker', 'Value': tag_enable})

    try:
        cwprint({'TagSet': tag_set})
        s3_client.put_bucket_tagging(Bucket=bucket_name, Tagging={'TagSet': tag_set})
        success = True
    except:
        cwprint_exc()

    if not enable and start_stepfn_execution:
        # call step function to complete edit activation
        stepfn_name = stepfn.get_stepfn_arn(None, "BucketDisableArn")

        try:
            sfn_client = boto3.client('stepfunctions')
            response = sfn_client.start_execution(
                stateMachineArn=stepfn_name,
                input=json.dumps({
                    'bucket': bucket_name,
                }),
                traceHeader="ShotLocker-Bucket-Disable"
            )
        except Exception as e:
            cwprint_exc()
            success = False

    return success


def is_shot_locker_bucket_valid(bucket_name, *, s3_client=None):
    buckets = get_shot_locker_bucket_list(s3_client=s3_client)
    return any([bucket_name == b['name'] for b in buckets])


def _add_bucket_upload_notification(bucket_name, *, s3_client=None):
    if not s3_client:
        s3_client = boto3.client('s3')

    config = s3_client.get_bucket_notification_configuration(Bucket=bucket_name)

    if 'ResponseMetadata' in config:
        del(config['ResponseMetadata'])

    if 'LambdaFunctionConfigurations' not in config or not isinstance(config['LambdaFunctionConfigurations'], list):
        config['LambdaFunctionConfigurations'] = []

    found = False
    for lfc in config['LambdaFunctionConfigurations']:
        if 'LambdaFunctionArn' in lfc:
            if 'ShotLocker-Upload-Edit' in lfc['LambdaFunctionArn']:
                found = True

    if not found:
        account_id = boto3.client('sts').get_caller_identity()["Account"]
        aws_partition = os.environ.get('AWS_PARTITION')
        aws_region = os.environ.get('AWS_REGION')
        arn = f'arn:{aws_partition}:lambda:{aws_region}:{account_id}:function:ShotLocker-Upload-Edit'

        for ext in [".xml", ".aaf", ".otio"]:
            notify = {
                'LambdaFunctionArn': arn,
                'Events': [ 's3:ObjectCreated:Put' ],
                'Filter': {
                    'Key': {
                        'FilterRules': [
                            {'Name': 'Prefix', 'Value': 'ShotLocker/Edits/'},
                            {'Name': 'Suffix', 'Value': ext},
                        ]
                    }
                }
            }

            config['LambdaFunctionConfigurations'].append(notify)

        cwprint({"description": "ShotLocker add_bucket_upload_notification",
                "bucket": bucket_name, 
                "put_bucket_notification_configuration": config,
                })

        s3_client.put_bucket_notification_configuration(Bucket=bucket_name, NotificationConfiguration=config)


def _remove_bucket_upload_notification(bucket_name, *, s3_client=None):
    if not s3_client:
        s3_client = boto3.client('s3')

    config = s3_client.get_bucket_notification_configuration(Bucket=bucket_name)

    if 'ResponseMetadata' in config:
        del(config['ResponseMetadata'])

    if 'LambdaFunctionConfigurations' not in config or not isinstance(config['LambdaFunctionConfigurations'], list):
        config['LambdaFunctionConfigurations'] = []

    func_config = []
    for lfc in config['LambdaFunctionConfigurations']:
        if 'LambdaFunctionArn' in lfc:
            if 'ShotLocker-Upload-Edit' not in lfc['LambdaFunctionArn']:
                func_config.append(lfc)

    config['LambdaFunctionConfigurations'] = func_config

    cwprint({"description": "ShotLocker remove_bucket_upload_notification",
            "bucket": bucket_name, 
            "put_bucket_notification_configuration": config,
            })

    s3_client.put_bucket_notification_configuration(Bucket=bucket_name, NotificationConfiguration=config)
