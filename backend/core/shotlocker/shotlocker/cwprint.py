# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import sys
import pprint
import traceback
import json


def cwprint(object, header:str=None):
    # CloudWatch pprint as a single log entry
    # CloudWatch accepts \r as newline for printing
    if isinstance(object, dict) or isinstance(object, list):
        object = json.dumps(object, default=str)
    s = pprint.pformat(object).replace('\n', '\r')
    if header:
        print(header+': \r'+s)
    else:
        print(s)
    return s


def cwprint_exc(header:str=None):
    strs = []
    if header:
        strs.append(header + "\n")
    exc_type, exc_value, exc_tb = sys.exc_info()
    strs.extend(traceback.format_exception(exc_type, exc_value, exc_tb))
    return cwprint(''.join(strs))

