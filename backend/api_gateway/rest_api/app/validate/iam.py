# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import re


def validate_iam_user_role_arn(arn:str, *, raise_exc:bool=False) -> bool:
    """ validates iam arn """
    pattern = "(^arn:(aws).*:iam::\d{12}:(user|role)/[A-Za-z0-9]+$)"
    results = re.match(pattern, arn)
    if not results and raise_exc:
        raise ValueError("IAM arn not valid")
    return results is not None

