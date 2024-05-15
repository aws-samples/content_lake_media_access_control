# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import datetime
import shotlocker
from shotlocker.log import log_entry
from shotlocker.s3_utils import write_json_to_s3


def lambda_handler(event, context):

    bucket = event['bucket']
    key = event['key']
    edit_id = event['edit_id']

    base, ext = os.path.splitext(os.path.basename(key))
    results_key = os.path.dirname(key) + "/processed/" + base + ".json"

    parts = key.split('/')
    if len(parts) != 4 or parts[0] != "ShotLocker" or parts[1] != 'Edits':
        log_entry(edit_id, 'ERROR: Bucket key improper format')
        raise ValueError('ERROR: Bucket key improper format')

    valid_exts = ['.xml', '.aaf', '.otio']
    if ext not in valid_exts:
        log_entry(edit_id, f"ERROR: import edit format {ext}, must be one of: {','.join(valid_exts)}")
        raise ValueError(f'Bucket key improper edit format ({ext})')

    log_entry(edit_id, f"Edit ({edit_id}) validated")

    # tag as ShotLocker 
    shotlocker.edit.set_shot_locker_bucket_edit(bucket, edit_id, enable=True, start_stepfn_execution=False)

    event['results_key'] = results_key
    results = {
        # lambda runs with UTC timestamp
        'create_time': datetime.datetime.now().isoformat() + "Z",
        'source': {
            's3_uri': f's3://{bucket}/{key}',
        },
        'results': {
            's3_uri': f's3://{bucket}/{results_key}',
        },
    }
    try:
        write_json_to_s3(results, bucket, results_key)
    except:
        log_entry(edit_id, f"ERROR: unable to write results.json")

    return event
