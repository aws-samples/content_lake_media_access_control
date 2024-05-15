# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import string
import secrets


def create_alphanumeric_random_string(length=10):
    alphabet = string.ascii_lowercase + string.digits
    access_token = ''.join(secrets.choice(alphabet) for i in range(length))
    return access_token


def create_access_token(length=10):
    """ access_token should be all lower case letters and numbers """
    return create_alphanumeric_random_string(length)


def get_access_token_from_s3_key(key):
    parts = key.split('/')
    if len(parts) == 4 or len(parts) == 5:
        if parts[0] == 'ShotLocker' and parts[1] == 'Edits':
            return parts[2]
    return None


