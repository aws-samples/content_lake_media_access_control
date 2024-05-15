# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import tempfile
import boto3
from shotlocker.log import log_entry
from shotlocker.cwprint import cwprint_exc
from shotlocker.s3_utils import read_json_from_s3, write_json_to_s3
import opentimelineio as otio


s3_client = boto3.client('s3')


def lambda_handler(event, context):
    bucket = event['bucket']
    key = event['key']
    edit_id = event['edit_id']
    results_key = event['results_key']

    try:
        results = read_json_from_s3(bucket, results_key, s3_client=s3_client)
    except:
        log_entry(edit_id, f"ERROR: unable to read results json")
        results = {}

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
    except Exception as e:
        log_entry(edit_id, f'ERROR getting object {key} from bucket {bucket}.')
        cwprint_exc(f'Error getting object {key} from bucket {bucket}.')
        raise e

    # get the contents of the object
    obj = response['Body'].read()

    base, ext = os.path.splitext(os.path.basename(key))

    # write it locally in a temp file
    tf = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    tf_name = tf.name
    tf.write(obj)
    tf.close()

    try:
        tl = otio.adapters.read_from_file(tf_name)
    except Exception as e:
        log_entry(edit_id, f'ERROR unable to process {key} from bucket {bucket}.')
        cwprint_exc(f'Error unable to process {key} from bucket {bucket}.')
        raise e

    # remove temp file
    os.unlink(tf_name)

    # processed edit file
    new_key = os.path.dirname(key) + "/processed/" + base + '-shotlocker-manifest.otio'
    log_entry(edit_id, f'Writing processed edit to {new_key}')

    data = otio.adapters.write_to_string(tl).encode()

    # write it back out as an otio file
    try:
        s3_client.put_object(Body=data, Bucket=bucket, Key=new_key)
    except Exception as e:
        log_entry(edit_id, f'ERROR writing object {new_key} to bucket {bucket}.')
        cwprint_exc(f'Error writing object {new_key} to bucket {bucket}.')
        raise e

    # write the manifest
    results['results']['manifest'] = f's3://{bucket}/{new_key}'
    try:
        write_json_to_s3(results, bucket, results_key, s3_client=s3_client)
    except:
        log_entry(edit_id, f"ERROR: unable to write results.json")

    event['original_key'] = key
    event['key'] = new_key

    return event

 