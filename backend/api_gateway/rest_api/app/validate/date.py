# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import datetime


def validate_date(check_date, *, raise_exc:bool=False):
    try:
        # throws ValueError
        datetime.date.fromisoformat(check_date)
        valid = True
    except ValueError:
        valid = False
        if raise_exc:
            raise

    return valid
