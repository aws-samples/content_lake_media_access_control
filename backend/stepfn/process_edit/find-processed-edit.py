# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import shotlocker


def lambda_handler(event, context):
    bucket = event.get('bucket')
    edit_id = event.get('edit_id')
    key = event.get('key')

    if not bucket or not edit_id:
        raise ValueError("Missing required parameters")

    if not key:
        results = shotlocker.edit.get_shot_locker_bucket_edit_info(bucket, edit_id, as_s3_uri=False)
        event['key'] = results['manifest']

    return event
