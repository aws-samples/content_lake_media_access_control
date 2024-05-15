# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3
from botocore.exceptions import ClientError
from .token import create_alphanumeric_random_string


def get_sid_name(access_token):
    return "ShotLocker" + access_token


def get_access_token_from_sid_name(sid_name):
    prefix = "ShotLocker"
    if sid_name.startswith(prefix):
        sub = sid_name[len(prefix):]
        if 'Index' in sub:
            sub = sub[:sub.index('Index')]
        return sub
    return None


def get_default_policy():
    bucket_policy = {
        'Version': '2012-10-17',
        'Statement': []
    }
    return json.dumps(bucket_policy)


def get_shot_locker_bucket_policy_as_json(bucket_name, *, s3_client=None):
    if not s3_client:
        s3_client = boto3.client('s3')
    try:
        result = s3_client.get_bucket_policy(Bucket=bucket_name)
    except ClientError as e:
        return None
    return result["Policy"]


def put_shot_locker_bucket_policy_as_json(bucket_name, bucket_policy, *, s3_client=None):
    if not s3_client:
        s3_client = boto3.client('s3')
    s3_client.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy)


def delete_shot_locker_bucket_policy_as_json(bucket_name, *, s3_client=None):
    if not s3_client:
        s3_client = boto3.client('s3')
    s3_client.delete_bucket_policy(Bucket=bucket_name)


def add_user_to_shot_locker_bucket_policy(
    bucket_name, 
    bucket_policy, 
    user_arn, 
    access_token, 
    *, 
    expired_date=None,
    s3_client=None
):
    if not bucket_policy:
        bucket_policy = get_default_policy()
    dict_policy = json.loads(bucket_policy)

    access_sid = get_sid_name(access_token)
    
    changed = False

    if 'Statement' not in dict_policy:
        dict_policy['Statement'] = []
        changed = True

    found_statement = False

    for statement in dict_policy['Statement']:
        if 'Sid' in statement and statement['Sid'].startswith(access_sid):
            if 'Principal' in statement and 'AWS' in statement['Principal']:
                if statement['Principal']['AWS'] == user_arn:
                    # found bucket policy for access_token
                   found_statement = True

    if not found_statement:
        # add new statement
        random_key = create_alphanumeric_random_string(8)

        # figure out current partition
        try:
            arn = boto3.client('sts').get_caller_identity().get('Arn')
            partition = arn.split()[1]
        except:
            partition = 'aws'

        policy = {
            'Sid': f"{access_sid}Index{random_key}",
            'Effect': 'Allow',
            'Action': 's3:GetObject',
            'Resource': f'arn:{partition}:s3:::{bucket_name}/*',
            'Principal': { "AWS": user_arn },
            'Condition': { "StringLike": { "s3:ExistingObjectTag/ShotLockerAccess": f"*{access_token}*" } }
        }
        if expired_date:
            policy['Condition']['DateLessThan'] = {"aws:CurrentTime": f"{expired_date}T23:59:59Z"}
        dict_policy['Statement'].append(policy)
        changed = True

    if changed:
        bucket_policy = json.dumps(dict_policy) 
        put_shot_locker_bucket_policy_as_json(bucket_name, bucket_policy, s3_client=s3_client)

    return bucket_policy 


def remove_user_from_shot_locker_bucket_policy(
    bucket_name, 
    bucket_policy, 
    user_arn, 
    access_token, 
    *, 
    s3_client=None
):
    if not bucket_policy:
        bucket_policy = get_default_policy()
    dict_policy = json.loads(bucket_policy)

    access_sid = get_sid_name(access_token)
    
    changed = False

    if 'Statement' not in dict_policy:
        dict_policy['Statement'] = []
        changed = True

    new_statements = []

    for statement in dict_policy['Statement']:
        if 'Sid' in statement and statement['Sid'].startswith(access_sid):
            
            # found bucket policy for access_token
            principal_user = None
            if 'Principal' in statement and 'AWS' in statement['Principal']:
                principal_user = statement['Principal']['AWS']

            if principal_user != user_arn:
                # user not in statement
                new_statements.append(statement)
            else:
                changed = True

        else:
            new_statements.append(statement)

    if changed:
        dict_policy['Statement'] = new_statements
        bucket_policy = json.dumps(dict_policy) 
        if not new_statements:
            delete_shot_locker_bucket_policy_as_json(bucket_name, s3_client=s3_client)
        else:
            put_shot_locker_bucket_policy_as_json(bucket_name, bucket_policy, s3_client=s3_client)

    return json.dumps(dict_policy)


def remove_shot_locker_bucket_access_policy(
    bucket_name, 
    bucket_policy, 
    access_token, 
    *, 
    s3_client=None
):
    """ Remove access token and all users from bucket policy """
    if not bucket_policy:
        bucket_policy = get_default_policy()
    dict_policy = json.loads(bucket_policy)

    access_sid = get_sid_name(access_token)
    
    changed = False

    if 'Statement' not in dict_policy:
        dict_policy['Statement'] = []
        changed = True

    new_statements = []

    for statement in dict_policy['Statement']:
        if 'Sid' in statement and statement['Sid'].startswith(access_sid):
            changed = True
        else:
            new_statements.append(statement)

    if changed:
        dict_policy['Statement'] = new_statements
        bucket_policy = json.dumps(dict_policy) 
        if not new_statements:
            delete_shot_locker_bucket_policy_as_json(bucket_name, s3_client=s3_client)
        else:
            put_shot_locker_bucket_policy_as_json(bucket_name, bucket_policy, s3_client=s3_client)

    return json.dumps(dict_policy)


def get_shot_locker_bucket_user_access_token_list(
    bucket_policy, 
    user_arn, 
    filter_access_token=None
):
    if not bucket_policy:
        bucket_policy = get_default_policy()
    dict_policy = json.loads(bucket_policy)

    access_sid = get_sid_name(filter_access_token) if filter_access_token else None
    
    if 'Statement' not in dict_policy:
        dict_policy['Statement'] = []

    user_in_statements = []

    for statement in dict_policy['Statement']:
        if 'Sid' in statement and statement['Sid'].startswith('ShotLocker'):
            if 'Principal' in statement and 'AWS' in statement['Principal']:
                principal_user = statement['Principal']['AWS']
                if access_sid:
                    if 'Sid' in statement and statement['Sid'].startswith(access_sid):
                        user_in_statements.append(get_access_token_from_sid_name(access_sid))
                elif 'Sid' in statement:
                    user_in_statements.append(get_access_token_from_sid_name(statement['Sid']))

    return user_in_statements


def get_shot_locker_bucket_user_access_list(bucket_policy, access_token, include_expired_date=False):
    """
    get a list of users in an bucket policy access token
    """
    if not bucket_policy:
        bucket_policy = get_default_policy()
    dict_policy = json.loads(bucket_policy)

    access_sid = get_sid_name(access_token)
    
    if 'Statement' not in dict_policy:
        dict_policy['Statement'] = []

    users = []

    for statement in dict_policy['Statement']:
        if 'Sid' in statement and statement['Sid'].startswith(access_sid):
            if 'Principal' in statement and 'AWS' in statement['Principal']:
                user = statement['Principal']['AWS']
                if include_expired_date:
                    expired = None
                    if 'Condition' in statement:
                        for k,v in statement['Condition'].items():
                            if k == 'DateLessThan':
                                if 'aws:CurrentTime' in v:
                                    expired = v['aws:CurrentTime'][:10]
                    users.append({
                        'user_role_arn': user,
                        'expired_date': expired
                    })
                else:
                    users.append(user)

    return users

