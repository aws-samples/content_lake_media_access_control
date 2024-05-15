# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Duration,
    aws_s3 as s3,
    RemovalPolicy,
)
from .security import require_tls_add_to_resource_policy


def create_access_log_bucket(stack):
    bucket = s3.Bucket(stack, 'ShotLocker-Access-Log-Bucket', 
        block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        removal_policy=RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
        object_ownership=s3.ObjectOwnership.OBJECT_WRITER,
        enforce_ssl=True,
        lifecycle_rules=[
            s3.LifecycleRule(
                enabled=True,
                expiration=Duration.days(1),
                noncurrent_version_expiration=Duration.days(1),
            ),
        ]
    )

    require_tls_add_to_resource_policy(bucket)

    return bucket


