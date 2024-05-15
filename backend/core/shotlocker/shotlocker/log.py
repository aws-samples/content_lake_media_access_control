# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
from datetime import datetime
import time
from typing import Any
from .cwprint import cwprint_exc
import boto3


def log_entry(
    id:str, 
    content:Any, 
    *, 
    region=None
):

    log_group_name = os.environ.get("LOG_GROUP_NAME")

    if not region:
        region = os.environ.get("AWS_REGION")

    now = datetime.now()
    isonow = now.strftime('%Y-%m-%dT%H:%M:%S')

    timestamp = int(round(time.time() * 1000))
    
    log = {
        "Id": id,
        "Active": True,
        'CreateTime': isonow + "Z",
        'Region': region
    }

    if isinstance(content, dict):
        log.update(content)
    elif isinstance(content, list):
        log['Message'] = ','.join(content)
    else:
        log['Message'] = content
    
    log_client = boto3.client('logs', region_name=region)

    try:
        log_client.create_log_stream(
            logGroupName=log_group_name,
            logStreamName=id,
        )
    except log_client.exceptions.ResourceAlreadyExistsException:
        pass

    response = log_client.put_log_events(
        logGroupName=log_group_name,
        logStreamName=id,
        logEvents=[
            {
                'timestamp': timestamp,
                'message': json.dumps(log, indent=2)
            },
        ],
    )


def get_log_entries(
    id:str, 
    *, 
    region=None
):
    log_group_name = os.environ.get("LOG_GROUP_NAME")

    if not region:
        region = os.environ.get('AWS_REGION')
    
    log_client = boto3.client('logs', region_name=region)

    events = []

    try:
        kwargs = {
            'logGroupName': log_group_name,
            'logStreamName': id,
            'startFromHead': True,
        }
        while True:
            resp = log_client.get_log_events(**kwargs)
            events.extend(resp['events'])
            if 'nextForwardToken' not in resp or resp['nextForwardToken'] == kwargs.get('nextToken'):
                break
            kwargs['nextToken'] = resp['nextForwardToken']
    except:
        cwprint_exc("Get Logs")

    entries = [e['message'] for e in events]

    # convert entries to json
    json_entries = []
    for e in entries:
        if isinstance(e, str):
            try:
                j = json.loads(e)
                json_entries.append(j)
            except:
                json_entries.append({"message":e})
        else:
            json_entries.append(e)

    return json_entries

