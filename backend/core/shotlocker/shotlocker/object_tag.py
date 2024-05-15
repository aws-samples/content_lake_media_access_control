# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from . import s3_utils
import boto3


def get_s3_object_tag_list(
    s3_uri, 
    *, 
    s3_client=None
):
    bucket, key = s3_utils.get_bucket_key_from_s3_uri(s3_uri)
    if not s3_client:
        s3_client = boto3.client('s3')
    response = s3_client.get_object_tagging(Bucket=bucket, Key=key)

    # if TagSet is empty, it returns an empty list
    return response['TagSet']


def put_s3_object_tag_list(
    s3_uri, 
    tag_list, 
    *, 
    s3_client=None
):
    bucket, key = s3_utils.get_bucket_key_from_s3_uri(s3_uri)
    if not s3_client:
        s3_client = boto3.client('s3')
    s3_client.put_object_tagging(Bucket=bucket,
                                 Key=key,
                                 Tagging={
                                     'TagSet': tag_list
                                 })


def get_shot_locker_access_token_list(tag_list=None):
    for tag in tag_list:
        if tag['Key'] == 'ShotLockerAccess':
            return tag['Value'].split(':') if tag['Value'] else []
    return []


def put_shot_locker_access_token_list(
    s3_uri, 
    access_token_list, 
    in_tag_list=None, 
    *, 
    s3_client=None
):
    tag_value = ':'.join(access_token_list)

    tag_list = in_tag_list
    if tag_list is None:
        tag_list = get_s3_object_tag_list(s3_uri, s3_client=s3_client)

    updated = False
    for tag in tag_list:
        if tag['Key'] == 'ShotLockerAccess':
            tag['Value'] = tag_value
            updated = True

    if not updated:
        tag_list.append({
            'Key': 'ShotLockerAccess',
            'Value': tag_value
        })

    put_s3_object_tag_list(s3_uri, tag_list, s3_client=s3_client)


def add_access_token_to_shot_locker_tag(
    s3_uri, 
    access_token, 
    *, 
    s3_client=None
) -> bool:
    added = False
    tag_list = get_s3_object_tag_list(s3_uri, s3_client=s3_client)
    access_token_list = get_shot_locker_access_token_list(tag_list)
    if access_token not in access_token_list:
        added = True
        access_token_list.append(access_token)
        put_shot_locker_access_token_list(s3_uri, access_token_list, tag_list, s3_client=s3_client)
    return added


def remove_access_token_from_shot_locker_tag(
    s3_uri, 
    access_token, 
    *, 
    s3_client=None
) -> bool:
    removed = False
    tag_list = get_s3_object_tag_list(s3_uri, s3_client=s3_client)
    access_token_list = get_shot_locker_access_token_list(tag_list)
    if access_token in access_token_list:
        removed = True
        access_token_list.remove(access_token)
        put_shot_locker_access_token_list(s3_uri, access_token_list, tag_list, s3_client=s3_client)
    return removed


def clear_all_access_tokens_from_shot_locker_tag(
    s3_uri, 
    *, 
    s3_client=None
):
    """ returns the list of access tokens removed (could be an empty list) """
    tag_list = get_s3_object_tag_list(s3_uri, s3_client=s3_client)
    access_token_list = get_shot_locker_access_token_list(tag_list)
    if access_token_list:
        put_shot_locker_access_token_list(s3_uri, [], tag_list, s3_client=s3_client)
    return access_token_list


def get_shot_locker_object_list(
    bucket_name, 
    access_token, 
    *, 
    s3_client=None
):
    object_list = []

    if not s3_client:
        s3_client = boto3.client('s3')
    objs = s3_client.list_objects_v2(Bucket=bucket_name)

    while True:
        for obj in objs['Contents']:
            response = s3_client.get_object_tagging(Bucket=bucket_name, Key=obj['Key'])
            for tag_set in response['TagSet']:
                if tag_set['Key'] == 'ShotLockerAccess':
                    if access_token in tag_set['Value']:
                        object_list.append(f"s3://{bucket_name}/{obj['Key']}")

        if 'NextContinuationToken' not in objs:
            break
        objs = s3_client.list_objects_v2(Bucket=bucket_name,
                                         ContinuationToken=objs['NextContinuationToken'])

    return object_list




