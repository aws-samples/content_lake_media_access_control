# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from aws_cdk import (
    Duration,
    aws_iam as iam,
    aws_lambda,
    aws_stepfunctions as stepfn,
    aws_stepfunctions_tasks as stepfn_tasks,
)
from .security import suppress_cdk_nag_errors_by_grant_readwrite


SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def create_bucket_step_functions(
    stack, 
    lambda_layers, 
    log_group
):
    environment = {
        "LOG_GROUP_NAME": log_group.log_group_name,
    }

    # Step 1: Disable Edits
    disable_fn = _create_disable_edits_function(stack, lambda_layers, environment)
    disable_job = _create_disable_edits_task(stack, disable_fn)

    # Step 2: Remove All Object Tags
    remove_fn = _create_remove_tags_function(stack, lambda_layers, environment)
    remove_job = _create_remove_tags_task(stack, remove_fn)

    # Bucket Disable Step Function definition
    chain = disable_job.next(remove_job)

    # Bucket Disable Create State Machine
    bucket_disable = stepfn.StateMachine(stack, 'ShotLocker-Bucket-Disable-StepFn', 
        state_machine_name='ShotLocker-Bucket-Disable-StepFn', 
        definition_body=stepfn.DefinitionBody.from_chainable(chain),
        logs=stepfn.LogOptions(
            destination=log_group,
            level=stepfn.LogLevel.ALL
        ),
        tracing_enabled=True,
    )

    suppress_cdk_nag_errors_by_grant_readwrite(bucket_disable, 'stepfn lambdas')

    return {'bucket_disable': bucket_disable}


def _create_disable_edits_function(stack, lambda_layers, environment):

    # lambda role
    lambda_role = iam.Role(stack, 'ShotLocker-Bucket-StepFns-DisableEdit-Role', 
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    lambda_role.add_to_policy(iam.PolicyStatement(
        actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        resources=[f"arn:{stack.partition}:logs:*:*:*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
        actions=["s3:GetBucketLocation",
                 "s3:GetBucketTagging",
                 "s3:GetObject",
                 "s3:GetObjectTagging",
                 "s3:ListBucket",
                 "s3:PutBucketTagging",
                 "s3:PutObject", 
                 "s3:PutObjectTagging" ],
        resources=[f"*"],
    ))
    suppress_cdk_nag_errors_by_grant_readwrite(lambda_role)

    with open(os.path.join(SCRIPT_DIRECTORY, "..", "stepfn", "bucket_disable", "disable-edits.py")) as fd:
        code = fd.read()

    fn = aws_lambda.Function(
        stack,
        id='ShotLocker-Disable-Edits',
        function_name='ShotLocker-Disable-Edits', 
        description='Disable Edits in a Content Lake',
        runtime=aws_lambda.Runtime.PYTHON_3_9,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(60),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=256, # MB
    )
    return fn


def _create_disable_edits_task(stack, lambda_fn, postfix=""):
    job = stepfn_tasks.LambdaInvoke(stack, 
        "ShotLocker-Disable-Edits-Task" + postfix,
        lambda_function=lambda_fn,
        output_path="$.Payload",
    )
    return job


def _create_remove_tags_function(stack, lambda_layers, environment):

    # lambda role
    lambda_role = iam.Role(stack, 'ShotLocker-Bucket-StepFns-RemoveTag-Role', 
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    lambda_role.add_to_policy(iam.PolicyStatement(
        actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        resources=[f"arn:{stack.partition}:logs:*:*:*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
        actions=["s3:GetBucketLocation",
                 "s3:GetBucketTagging",
                 "s3:GetObject",
                 "s3:GetObjectTagging",
                 "s3:ListBucket",
                 "s3:PutBucketTagging",
                 "s3:PutObject",
                 "s3:PutObjectTagging",],
        resources=[f"*"],
    ))
    suppress_cdk_nag_errors_by_grant_readwrite(lambda_role)

    with open(os.path.join(SCRIPT_DIRECTORY, "..", "stepfn", "bucket_disable", "remove-object-tags.py")) as fd:
        code = fd.read()

    fn = aws_lambda.Function(
        stack,
        id='ShotLocker-Remove-Tags',
        function_name='ShotLocker-Remove-Tags',
        description='Remove All the Object Tags in a Content Lake',
        runtime=aws_lambda.Runtime.PYTHON_3_9,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(900),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=1024, # MB
    )
    return fn


def _create_remove_tags_task(stack, lambda_fn, postfix=""):
    job = stepfn_tasks.LambdaInvoke(stack, 
        'ShotLocker-Remove-Tags-Task' + postfix,
        lambda_function=lambda_fn,
        output_path="$.Payload",
    )
    return job
