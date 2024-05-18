# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Reference: https://github.com/AcademySoftwareFoundation/OpenTimelineIO/blob/main/examples/conform.py

import os
import time
import urllib
import urllib.parse
from shotlocker.log import log_entry
from shotlocker.cwprint import cwprint_exc
from shotlocker.s3_utils import read_json_from_s3, write_json_to_s3
import shotlocker.s3_utils
import shotlocker.otio
import boto3
import opentimelineio as otio


s3_client = boto3.client('s3')


def _find_media_in_content_lake(bucket, media_files, first_frame_files):

    def _content_lake_objects(object_list):
        nonlocal bucket
        nonlocal media_files
        nonlocal first_frame_files

        for object in object_list:

            fullpath = f's3://{bucket}/{object}'
            base = os.path.basename(object)

            if base in media_files and not media_files[base]:
                # if found the file and not yet saved it
                media_files[base] = fullpath
            elif base in first_frame_files:
                # if the file a first frame of a frame range?
                if not media_files[first_frame_files[base]]:
                    media_files[first_frame_files[base]] = os.path.dirname(fullpath) + "/" + first_frame_files[base]

    shotlocker.s3_utils.list_all_objects(bucket, 
                                         s3_client=s3_client, 
                                         names_only=True, 
                                         recursive=True, 
                                         content_callback_fn=_content_lake_objects)


def _find_media_root_in_content_lake(bucket, media_files, media_files_root):
    """ 
    Find media files that have the same root base name but different extensions. Only run
    after not finding the matching full base name.
    """

    def _content_lake_objects(object_list):
        nonlocal bucket
        nonlocal media_files
        nonlocal media_files_root

        for object in object_list:

            fullpath = f's3://{bucket}/{object}'
            base = os.path.basename(object)
            root, _ = os.path.splitext(base)

            if root in media_files_root and not media_files[media_files_root[root]]:
                # if found a media file with different extension 
                media_files[media_files_root[root]] = fullpath

    shotlocker.s3_utils.list_all_objects(bucket, 
                                         s3_client=s3_client, 
                                         names_only=True, 
                                         recursive=True, 
                                         content_callback_fn=_content_lake_objects)


def lambda_handler(event, context):

    bucket = event['bucket']
    key = event['key']
    edit_id = event['edit_id']
    results_key = event['results_key']

    # option: keep all s3 references whether in this content lake bucket or not
    keep_s3_ref = event.get('keep_s3_ref', False)

    # option: replace any external references that are missing with missing references
    replace_missing = event.get('replace_missing', True)

    start_time = time.time()

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
        raise 

    # get the contents of the object
    obj = response['Body'].read().decode()

    try:
        timeline = otio.adapters.read_from_string(obj)
    except Exception as e:
        log_entry(edit_id, f'ERROR unable to process {key} from bucket {bucket}.')
        cwprint_exc(f'Error unable to process {key} from bucket {bucket}.')
        raise e

    total = 0
    count = 0
    exists = 0

    # get a list of clip filenames in the edit
    media_files = {}
    first_frame_files = {}
    root_media_files = {}
    original_media_files = {}

    for clip in timeline.find_clips():

        if not shotlocker.otio.has_media_reference(clip):
            continue

        filename = shotlocker.otio.find_media_url_in_clip(clip)
        if not filename:
            log_entry(edit_id, f'Warning: {clip.name} - Missing Reference, skipping...')
            continue

        basename = os.path.basename(filename.replace('\\', '/'))

        # if the reference is a frame range, look for the first frame of the
        # range to identify the location of the files in the content lake
        if shotlocker.frame_range.has_frame_range(basename):
            frames = shotlocker.frame_range.expand_filename_frame_range(basename, check_exist=False)
            if len(frames):
                first_frame_files[frames[0]] = basename
        else:
            # FUTURE: get clip frame range and look for individual frames
            # this is when you edit a proxy and then want to conform to the frames
            pass

        total += 1

        if basename not in media_files:
            media_files[basename] = None

            # if the filename URL already in S3, check
            url = urllib.parse.urlparse(filename)
            if url.scheme == 's3':
                # if in the content lake or keeping all s3 reference
                if url.netloc == bucket or keep_s3_ref:
                    media_files[basename] = filename

            # save the root media filename so can look up media files with different extensions
            root,_ = os.path.splitext(basename)
            root_media_files[root] = basename

            # save the original media filename
            original_media_files[basename] = filename

    # make sure there is media to find
    if not len(media_files.keys()):
        log_entry(edit_id, f'Warning: No media references found in the edit')
        return event

    # check to see if the media is already referenced
    if not any(v is None for v in media_files.values()):
        log_entry(edit_id, f'Warning: All media references ({total}) already reference Amazon S3')
        return event

    # find the media in the content lake
    _find_media_in_content_lake(bucket, media_files, first_frame_files)

    # if some of the media files have not been found, try searching for the media base name root
    if not all(media_files.values()):
        _find_media_root_in_content_lake(bucket, media_files, root_media_files)

    # replace the clip filenames with one in the content lake
    replaced_with_missing = {}
    for clip in timeline.find_clips():

        if not shotlocker.otio.has_media_reference(clip):
            continue

        filename = shotlocker.otio.find_media_url_in_clip(clip)
        if not filename:
            continue

        basename = os.path.basename(filename.replace('\\', '/'))
         
        new_path = media_files[basename]
        if not new_path:
            # if no media is found, keep going
            log_entry(edit_id, f'Warning: Clip {clip.name} - Missing "{basename}" in Content Lake, Replacing.')

            # replace with Missing Reference
            if replace_missing:
                clip.media_reference = otio.schema.MissingReference(
                    basename, 
                    metadata={"ShotLocker_OTIO": {"Media Url": filename}})

                replaced_with_missing[clip.name] = filename

            continue

        # relink to the found path
        if filename != new_path:
            clip.media_reference.target_url = new_path
            count += 1
        else:
            exists += 1

    log_entry(edit_id, f'Updated {count} of {total-exists} Media Reference Target URLs in edit')
    if exists:
        log_entry(edit_id, f'{exists} Media Reference Target URLs already reference Amazon S3')

    if count:
        # write it back out 
        data = otio.adapters.write_to_string(timeline).encode()

        try:
            s3_client.put_object(Body=data, Bucket=bucket, Key=key)
        except Exception as e:
            log_entry(edit_id, f'ERROR writing updated object {key} to bucket {bucket}.')
            cwprint_exc(f'Error writing updated object {key} to bucket {bucket}.')
            raise e
    else:
        log_entry(edit_id, f'Warning: No Media Reference Target URLs found in edit')

    # write the file check results
    results['conform_media_files'] = media_files
    results['original_media_files'] = original_media_files
    results['replaced_with_missing'] = replaced_with_missing
    try:
        write_json_to_s3(results, bucket, results_key, s3_client=s3_client)
    except:
        log_entry(edit_id, f"ERROR: unable to write results.json")

    end_time = time.time()

    log_entry(edit_id, f'Conform to Amazon S3 media complete ({round(end_time-start_time)} seconds)')

    return event
