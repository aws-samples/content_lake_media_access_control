# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import shotlocker
from shotlocker.cwprint import cwprint_exc


def lambda_handler(event, context):
    bucket = event.get('bucket')
    edit_id = event.get('edit_id')

    # remove edit access from bucket
    try:
        policy = shotlocker.bucket_policy.get_shot_locker_bucket_policy_as_json(bucket)
        shotlocker.bucket_policy.remove_shot_locker_bucket_access_policy(bucket, policy, edit_id)
    except Exception as e:
        cwprint_exc()
        raise

    return event