# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import time

from concurrent.futures import ThreadPoolExecutor

import boto3
import opentimelineio as otio
import shotlocker
import shotlocker.otio
from shotlocker.log import log_entry
from shotlocker.cwprint import cwprint_exc
from shotlocker.s3_utils import read_json_from_s3, write_json_to_s3


def lambda_handler(event, context):

    bucket = event['bucket']
    key = event['key']
    edit_id = event['edit_id']
    results_key = event.get('results_key')
    
    # option: add or remove tags
    mode = event.get('mode', 'add')
    add_access_token = mode == "add"

    start_time = time.time()

    log_entry(edit_id, f'Tagging ({mode}) Amazon S3 objects started')

    if not bucket or not key or not edit_id:
        msg = f'object-tag-access-token: missing required fields'
        raise ValueError(msg)

    s3_client = boto3.client('s3')

    results = {}
    if results_key:
        try:
            results = read_json_from_s3(bucket, results_key, s3_client=s3_client)
        except:
            log_entry(edit_id, f"ERROR: unable to read results json")

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
    except Exception as e:
        log_entry(edit_id, f'Error getting object {key} from bucket {bucket}.')
        cwprint_exc(f'Error getting object {key} from bucket {bucket}.')
        raise

    # get the contents of the object
    obj = response['Body'].read().decode()

    try:
        timeline = otio.adapters.read_from_string(obj)
    except Exception as e:
        log_entry(edit_id, f'ERROR unable to process {key} from bucket {bucket}.')
        cwprint_exc(f'Error unable to process {key} from bucket {bucket}.')
        raise

    file_check = {}

    total_files = set()
    files_to_tag = set()

    for clip in timeline.find_clips():
        name = clip.name

        if not shotlocker.otio.has_media_reference(clip):
            continue

        filename = shotlocker.otio.find_media_url_in_clip(clip)
        if not filename:
            continue

        try:
            filenames = shotlocker.frame_range.expand_filename_frame_range(
                filename,
                s3_client=s3_client, 
                check_exist=True)
        except Exception as e:
            msg = f'Error: Clip {name} - Unable to expand file {filename}'
            log_entry(edit_id, msg)
            log_entry(edit_id, f'Error {e}')

            cwprint_exc(msg)

            file_check[name] = [{
                'exists': False, 
                's3_uri': None,
            }]
            continue

        print(f'{name} - {filename} - {len(filenames)} files')
        total_files.update(filenames)

        check = []
        for s3_uri,exists in filenames:
            check.append({
                'exists': exists, 
                's3_uri': s3_uri,
            })
            if exists:
                files_to_tag.add(s3_uri)

        file_check[name] = check

    def _add_access_token(s3_uri, access_token, s3_client):
        shotlocker.object_tag.add_access_token_to_shot_locker_tag(s3_uri, access_token, s3_client=s3_client) 

    def _remove_access_token(s3_uri, access_token, s3_client):
        if shotlocker.object_tag.remove_access_token_from_shot_locker_tag(s3_uri, access_token, s3_client=s3_client):
            print(f"Removed access token {access_token} from {s3_uri}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        for s3_uri in files_to_tag:
            print(f"Object {mode} tag {s3_uri}")
            if add_access_token:
                executor.submit(_add_access_token, s3_uri, edit_id, s3_client) 
            else:
                executor.submit(_remove_access_token, s3_uri, edit_id, s3_client) 

    end_time = time.time()

    log_entry(edit_id, f'Total files to {mode} tag: {len(total_files)}')
    log_entry(edit_id, f'Total files tagged: {len(files_to_tag)}')
    log_entry(edit_id, f'Tagging ({mode}) Amazon S3 objects completed ({round(end_time-start_time)} seconds)')

    # write the file check results
    results['object_tag'] = file_check
    results['files_tagged'] = list(files_to_tag)
    if results_key:
        try:
            write_json_to_s3(results, bucket, results_key, s3_client=s3_client)
        except:
            log_entry(edit_id, f"ERROR: unable to write results.json")

    return event

 
