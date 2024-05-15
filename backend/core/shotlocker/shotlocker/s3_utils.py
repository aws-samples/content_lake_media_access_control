# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
from .cwprint import cwprint_exc
import boto3
from botocore.exceptions import ClientError


def get_enabled_tag_value_list():
    return ('Enable', 'enable', 'Enabled', 'enabled', 'True', 'true', 't', '1', 'On', 'on')


def get_bucket_key_from_s3_uri(s3_uri):
    """
    return pair (bucket, key)
    """
    parts = s3_uri.replace("s3://", "").split("/", 2)
    
    # access point?  Access point bucket name is an arn with a slash in it
    if 'access_point' in parts[0]:
        return (parts[0] + '/' + parts[1], parts[2])

    return (parts[0], parts[1] + '/' + parts[2])


def does_s3_object_exist(s3_uri, *, s3_client=None):
    bucket, key = get_bucket_key_from_s3_uri(s3_uri)
    if not s3_client:
        s3_client = boto3.client('s3')
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
    except ClientError:
        return False
    return True


def list_all_objects(
    bucket:str, 
    prefix:str='', 
    *, 
    s3_client=None, 
    recursive=False, 
    names_only=True,
    content_callback_fn=None
):

    object_list = []

    if not s3_client:
        s3_client = boto3.client('s3')

    delimiter = '' if recursive else '/'

    try:
        objs = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter=delimiter)
    except:
        print(f"shotlocker.s3_utils.list_all_objects: ERROR accessing bucket {bucket} prefix {prefix} delimiter {delimiter}")
        raise

    while True:
        # Contents key only appears if there are actual contents
        if 'Contents' not in objs:
            break

        latest_objs = []
        for obj in objs['Contents']:
            if names_only:
                latest_objs.append(obj['Key'])
            else:
                latest_objs.append(obj)

        if content_callback_fn:
            content_callback_fn(latest_objs)

        object_list.extend(latest_objs)

        if 'NextContinuationToken' not in objs:
            break

        objs = s3_client.list_objects_v2(Bucket=bucket, 
                                         Prefix=prefix,
                                         Delimiter=delimiter,
                                         ContinuationToken=objs['NextContinuationToken'])

    return object_list


def list_all_prefixes(
    bucket:str, 
    prefix:str='', 
    *, 
    s3_client=None, 
    recursive=False
):

    prefix_list = []

    if not s3_client:
        s3_client = boto3.client('s3')

    delimiter = '' if recursive else '/'

    objs = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter=delimiter)

    if 'CommonPrefixes' in objs:
        for obj in objs['CommonPrefixes']:
            prefix_list.append(obj['Prefix'])

    return prefix_list


def read_json_from_s3(
    bucket,
    s3_key,
    *,
    s3_client=None
):
    if not s3_client:
        s3_client = boto3.client('s3')

    try:
        response = s3_client.get_object(Bucket=bucket, Key=s3_key)
    except Exception as e:
        cwprint_exc(f'Error getting object {s3_key} from bucket {bucket}.')
        raise 

    # get the contents of the object
    obj = response['Body'].read().decode()

    return json.loads(obj)


def write_json_to_s3(
    json_dict, 
    bucket,
    s3_key,
    *,
    s3_client=None
):
    if not s3_client:
        s3_client = boto3.client('s3')

    # write the file check results
    try:
        data = json.dumps(json_dict, indent=4).encode()
        s3_client.put_object(Body=data, Bucket=bucket, Key=s3_key)
    except Exception as e:
        cwprint_exc(f'Error writing updated object {s3_key} to bucket {bucket}.')
        raise

