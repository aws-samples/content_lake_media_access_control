# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from aws_cdk import (
    Duration,
    aws_iam as iam,
    aws_lambda,
)
from .security import suppress_cdk_nag_errors_by_grant_readwrite

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def create_upload_edit_function(
    stack, 
    lambda_layers, 
    log_group, 
    process_edit_stepfn
):

    # upload edit lambda role
    lambda_role = iam.Role(stack, 'ShotLocker-Upload-Edit-Role', 
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      resources=[f"arn:{stack.partition}:logs:*:*:*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["states:StartExecution",],
      resources=[process_edit_stepfn.state_machine_arn],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["ssm:GetParameter",],
      resources=["*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["s3:GetBucketLocation",
               "s3:GetBucketTagging",
               "s3:ListAllMyBuckets",
               "s3:ListBucket",],
      resources=[f"arn:{stack.partition}:s3:::*", 
                 f"arn:{stack.partition}:s3:::*/*"],
    ))

    with open(os.path.join(SCRIPT_DIRECTORY, "..", "upload_edit", "s3-put-object-lambda-start-stepfn.py")) as fd:
        code = fd.read()

    environment = {
        "LOG_GROUP_NAME": log_group.log_group_name,
        "PROCESS_EDIT_STEPFN_ARN": process_edit_stepfn.state_machine_arn,
    }

    upload_fn = aws_lambda.Function(
        stack,
        id='ShotLocker-Upload-Edit',
        function_name='ShotLocker-Upload-Edit',
        description='Shot Locker triggered lambda when Edit is Uploaded',
        runtime=aws_lambda.Runtime.PYTHON_3_9,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(10),
        environment = environment,
        layers=lambda_layers,
        retry_attempts=0,
        memory_size=128, # 128MB
        tracing=aws_lambda.Tracing.ACTIVE
    )

    # enable S3 to invoke lambda
    # lock it down only to the install account so not be open to the Confused Deputy Attack
    upload_fn.add_permission(id="ShotLocker-Upload-Edit-S3-Invoke-Permission",
                             action='lambda:InvokeFunction',
                             principal=iam.ServicePrincipal("s3.amazonaws.com"),
                             source_account=f'{stack.account}',
                             source_arn=f'arn:{stack.partition}:s3:::*'
                            )

    suppress_cdk_nag_errors_by_grant_readwrite(lambda_role)

    return upload_fn

