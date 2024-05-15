# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import shotlocker
from shotlocker.log import log_entry


s3_client = boto3.client('s3')


def lambda_handler(event, context):
    bucket = event['bucket']

    s3_client = boto3.client('s3')

    edits = shotlocker.edit.get_shot_locker_bucket_edit_detailed_list(bucket, include_inactive=False, s3_client=s3_client)

    for edit in edits:
        edit_id = edit['name']
        if shotlocker.edit.set_shot_locker_bucket_edit(bucket, edit_id, enable=False, s3_client=s3_client, start_stepfn_execution=False):
            print(f"Edit ({edit_id}) is disabled")
            log_entry(edit_id, f"Edit ({edit_id}) is disabled (bucket was disabled)")
        else:
            print("ERROR: Unable to disable Edit ({edit_id})")
            log_entry(edit_id, f"ERROR: Unable to disable Edit ({edit_id})")

    return event

