# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
import shotlocker


def lambda_handler(event, context):
    bucket = event['bucket']

    s3_client = boto3.client('s3')

    objects= shotlocker.s3_utils.list_all_objects(bucket, 
                                                  s3_client=s3_client, 
                                                  names_only=True, 
                                                  recursive=True) 

    print(f"Checking {len(objects)} objects in bucket {bucket}")

    def _remove_all_access_tokens(s3_uri, s3_client):
        if shotlocker.object_tag.clear_all_access_tokens_from_shot_locker_tag(s3_uri, s3_client=s3_client):
            print(f"Removed Access tokens from {s3_uri}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        for object in objects:
            s3_uri = f's3://{bucket}/{object}'
            executor.submit(_remove_all_access_tokens, s3_uri, s3_client) 

    return event
