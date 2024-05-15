# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
from .log import log_entry


def get_stepfn_arn(edit_id, arn_config):
    # retrieve the arn for step function
    ssm_client = boto3.client("ssm")
    try:
        response = ssm_client.get_parameter(Name=f"/ShotLocker/Config/{arn_config}")
    except:
        msg = f"ERROR: unable to find Step Function Arn ({arn_config})."
        if edit_id:
            log_entry(edit_id, msg)
        raise 

    if 'Parameter' in response and 'Value' in response['Parameter']:
        value = response['Parameter']['Value']
    else:
        msg = f"ERROR: unable to retrieve Step Function Arn ({arn_config})."
        if edit_id:
            log_entry(edit_id, msg)
        raise ValueError(msg)

    return value
