#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import aws_cdk as cdk

try:
    import cdk_nag as nag
except:
    nag = None

from backend.stack.shotlocker_stack import ShotLockerStack


app = cdk.App()

config = app.node.try_get_context("config")
settings = app.node.try_get_context(config)

# validate there is a postfix
if 'postfix' not in settings or not settings['postfix']:
    raise ValueError("Configuration Settings must have a unique postfix.")

ShotLockerStack(app, "ShotLocker-Stack")

if 'run_cdk_nag' in settings and settings['run_cdk_nag']:
    if nag:
        cdk.Aspects.of(app).add(nag.AwsSolutionsChecks(verbose=True))
    else:
        print("CDK NAG NOT installed")

app.synth()
