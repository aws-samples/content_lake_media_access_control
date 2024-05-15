# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import re
from . import s3_utils


def has_frame_range(s3_uri) -> bool:
    # file name ranges use format PREFIX.[0001-0005].exr format
    parts = re.split('\[|\]', s3_uri)
    return len(parts) == 3


def frame_ranges(s3_uri):
    # return either None if no range or tuple pair of ints
    parts = re.split('\[|\]', s3_uri)
    if len(parts) != 3:
        return None
    frame_range = parts[1].split('-')
    if len(frame_range) != 2:
        return None
    return (int(frame_range[0]), int(frame_range[1])+1)


def expand_filename_frame_range(
    s3_uri, 
    *, 
    s3_client=None,
    check_exist=False,
    bucket=None
):
    # file name ranges use format PREFIX.[0001-0005].exr format
    parts = re.split('\[|\]', s3_uri)
    if len(parts) != 3:
        # this means the s3_uri doesn't contain a frame range
        if check_exist:
            return [(s3_uri, s3_utils.does_s3_object_exist(s3_uri, s3_client=s3_client))]
        else:
            return [s3_uri]

    frame_range = parts[1].split('-')
    if len(frame_range) != 2:
        return [s3_uri]

    # leading zero number size
    leading_zero_size = 0
    if frame_range[0][0] == '0' or frame_range[1][0] == '0':
        leading_zero_size = max(len(frame_range[0]), len(frame_range[1]))

    filenames = []
    for frame_number in range(int(frame_range[0]), int(frame_range[1])+1):
        frame_number_str = str(frame_number).zfill(leading_zero_size) if leading_zero_size else str(frame_number)
        filenames.append(parts[0] + frame_number_str + parts[2])

    # if just getting the list of filenames
    if not check_exist:
       return filenames

    # strip protocol
    key = s3_uri
    if s3_uri.startswith('s3://'):
        parts = s3_uri[5:].split('/')
        bucket = parts[0]
        key = '/'.join(parts[1:])

    if not bucket:
       return filenames

    prefix = '/'.join(key.split('/')[:-1]) + '/'

    objects = set([f's3://{bucket}/{fn}' for fn in s3_utils.list_all_objects(bucket, prefix, s3_client=s3_client)])

    return [(fn, fn in objects) for fn in filenames]
        


