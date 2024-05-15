# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import urllib.parse
import boto3
import shotlocker
from shotlocker.log import log_entry
from shotlocker.cwprint import cwprint_exc


sfn_client = boto3.client('stepfunctions')


def lambda_handler(event, context):

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    parts = key.split('/')
    # ignore the processed otio file (len(parts)==5)
    if len(parts) != 4 or parts[0] != "ShotLocker" or parts[1] != "Edits":
        return

    if not shotlocker.bucket.is_shot_locker_bucket_valid(bucket):
        raise IOError("Shot Locker bucket is not enabled")

    edit_id = parts[2]

    name = 'ShotLocker-Put-Object-StepFn-' + edit_id
    
    log_entry(edit_id, f"Uploaded Bucket: {bucket} Edit: {key}")

    input = {
        'bucket': bucket,
        'key': key,
        'edit_id': edit_id,
    }

    process_edit_arn = shotlocker.stepfn.get_stepfn_arn(edit_id, "ProcessEditArn")

    try:
        response = sfn_client.start_execution(
            stateMachineArn=process_edit_arn,
            name=name,
            input=json.dumps(input),
            traceHeader='ShotLocker-Upload-Edit'
        )
    except Exception as e:
        cwprint_exc(f'Error put object {key} to bucket {bucket}: start step failed')
        log_entry(edit_id, f"ERROR: unable to put object {key} in {bucket}")
        raise e

    log_entry(edit_id, f"Starting Step Function: {name}")
    print(f"ShotLocker Upload Edit: {name}, Execution ARN: {response['executionArn']}")

    return response['executionArn']

