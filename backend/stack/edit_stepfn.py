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


def create_edit_step_functions(
    stack, 
    lambda_layers, 
    log_group
):

    environment = {
        "LOG_GROUP_NAME": log_group.log_group_name,
    }

    # Step 1: Validate the S3 Key 
    validate_fn = _create_validate_s3_function(stack, lambda_layers, environment)
    validate_job = _create_validate_s3_task(stack, validate_fn)

    # Step 2: Convert the Edit to OpenTimelineIO
    convert_fn = _create_convert_to_otio_function(stack, lambda_layers, environment)
    convert_job = _create_convert_to_otio_task(stack, convert_fn)

    # Step 3: Conform S3 Media
    conform_fn = _create_conform_s3_media_function(stack, lambda_layers, environment)
    conform_job = _create_conform_s3_media_task(stack, conform_fn)

    # Step 4: Tag Objects in S3
    tag_fn = _create_s3_object_tag_function(stack, lambda_layers, environment)
    tag_job = _create_s3_object_tag_task(stack, tag_fn)

    # Process Edit Step Function definition
    chain = validate_job.next(convert_job).next(conform_job).next(tag_job)

    # Process Edit Create State Machine
    process_edit = stepfn.StateMachine(stack, 'ShotLocker-Process-Edit-StepFn', 
        state_machine_name='ShotLocker-Process-Edit-StepFn', 
        definition_body=stepfn.DefinitionBody.from_chainable(chain),
        logs=stepfn.LogOptions(
            destination=log_group,
            level=stepfn.LogLevel.ALL
        ),
        tracing_enabled=True,
    )

    # Add Access Step Function
    find_fn = _create_find_processed_edit_function(stack, lambda_layers, environment)
    find_job = _create_find_processed_edit_task(stack, find_fn, "-Add")
    tag_job = _create_s3_object_tag_task(stack, tag_fn, "-Add")

    # Add Access Step Function definition
    chain = find_job.next(tag_job)

    # Add Access Edit Create State Machine
    add_access = stepfn.StateMachine(stack, 'ShotLocker-Add-Edit-Access-StepFn', 
        state_machine_name='ShotLocker-Add-Edit-Access-StepFn', 
        definition_body=stepfn.DefinitionBody.from_chainable(chain),
        logs=stepfn.LogOptions(
            destination=log_group,
            level=stepfn.LogLevel.ALL
        ),
        tracing_enabled=True,
    )

    # Remove Access Step Function
    rm_fn = _create_remove_bucket_access_function(stack, lambda_layers, environment)
    rm_job = _create_remove_bucket_access_task(stack, rm_fn, "-Remove")
    tag_job = _create_s3_object_tag_task(stack, tag_fn, "-Remove")

    # Remove Access Step Function definition
    chain = rm_job.next(tag_job)

    # Remove Access Edit Create State Machine
    remove_access = stepfn.StateMachine(stack, 'ShotLocker-Remove-Edit-Access-StepFn', 
        state_machine_name='ShotLocker-Remove-Edit-Access-StepFn', 
        definition_body=stepfn.DefinitionBody.from_chainable(chain),
        logs=stepfn.LogOptions(
            destination=log_group,
            level=stepfn.LogLevel.ALL
        ),
        tracing_enabled=True,
    )

    suppress_cdk_nag_errors_by_grant_readwrite(process_edit, 'stepfn lambdas')
    suppress_cdk_nag_errors_by_grant_readwrite(add_access, 'stepfn lambdas')
    suppress_cdk_nag_errors_by_grant_readwrite(remove_access, 'stepfn lambdas')

    return {
        'process_edit': process_edit, 
        'add_access': add_access, 
        'remove_access': remove_access, 
    }


def _create_validate_s3_function(stack, lambda_layers, environment):

    # lambda role
    lambda_role = iam.Role(stack, 'ShotLocker-Edit-Validate-S3-Role', 
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
                 "s3:ListAllMyBuckets",
                 "s3:ListBucket",
                 "s3:PutBucketTagging",
                 "s3:PutObject",
                 "s3:PutObjectTagging",],
        resources=["*"],
    ))
    suppress_cdk_nag_errors_by_grant_readwrite(lambda_role)

    with open(os.path.join(SCRIPT_DIRECTORY, "..", "stepfn", "process_edit", "validate-content-lake-edit-s3-key.py")) as fd:
        code = fd.read()

    validate_fn = aws_lambda.Function(
        stack,
        id='ShotLocker-Validate-S3',
        function_name='ShotLocker-Validate-S3', 
        description='Validate Content Lake edit S3 key',
        runtime=aws_lambda.Runtime.PYTHON_3_9,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(15),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=128, # MB
    )
    return validate_fn


def _create_validate_s3_task(stack, validate_fn, postfix=""):
    validate_job = stepfn_tasks.LambdaInvoke(stack, 
        "ShotLocker-Validate-S3-Task" + postfix,
        lambda_function=validate_fn,
        output_path="$.Payload",
    )
    return validate_job


def _create_convert_to_otio_function(stack, lambda_layers, environment):

    # lambda role
    lambda_role = iam.Role(stack, 'ShotLocker-Edit-Convert-OTIO-Role', 
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    lambda_role.add_to_policy(iam.PolicyStatement(
        actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        resources=[f"arn:{stack.partition}:logs:*:*:*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
        actions=[ "s3:GetObject", "s3:ListBucket", "s3:PutObject" ],
        resources=["*"],
    ))
    suppress_cdk_nag_errors_by_grant_readwrite(lambda_role)

    with open(os.path.join(SCRIPT_DIRECTORY, "..", "stepfn", "process_edit", "convert-to-otio.py")) as fd:
        code = fd.read()

    convert_fn = aws_lambda.Function(
        stack,
        id='ShotLocker-Convert-Edit-to-OTIO',
        function_name='ShotLocker-Convert-Edit-to-OTIO',
        description='Convert Edit file to Open Timeline IO json file',
        runtime=aws_lambda.Runtime.PYTHON_3_9,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(60),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=1024, # MB
    )
    return convert_fn


def _create_convert_to_otio_task(stack, convert_fn, postfix=""):
    convert_job = stepfn_tasks.LambdaInvoke(stack, 
        'ShotLocker-Convert-Edit-to-OTIO-Task' + postfix,
        lambda_function=convert_fn,
        output_path="$.Payload",
    )
    return convert_job


def _create_conform_s3_media_function(stack, lambda_layers, environment):

    # lambda role
    lambda_role = iam.Role(stack, 'ShotLocker-Edit-Conform-Media-Role', 
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
                 "s3:ListAllMyBuckets",
                 "s3:ListBucket",
                 "s3:PutBucketTagging",
                 "s3:PutObject",
                 "s3:PutObjectTagging",],
        resources=["*"],
    ))
    suppress_cdk_nag_errors_by_grant_readwrite(lambda_role)

    with open(os.path.join(SCRIPT_DIRECTORY, "..", "stepfn", "process_edit", "conform-s3-media.py")) as fd:
        code = fd.read()

    conform_fn = aws_lambda.Function(
        stack,
        id='ShotLocker-Conform-S3-Media',
        function_name='ShotLocker-Conform-S3-Media',
        description='Conform Edit to S3 media',
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
    return conform_fn


def _create_conform_s3_media_task(stack, conform_fn, postfix=""):
    conform_job = stepfn_tasks.LambdaInvoke(stack, 
        'ShotLocker-Conform-S3-Media-Task' + postfix,
        lambda_function=conform_fn,
        output_path="$.Payload",
    )
    return conform_job


def _create_s3_object_tag_function(stack, lambda_layers, environment):

    # lambda role
    lambda_role = iam.Role(stack, 'ShotLocker-Edit-Object-Tag-Role', 
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
                 "s3:ListAllMyBuckets",
                 "s3:ListBucket",
                 "s3:PutBucketTagging",
                 "s3:PutObject",
                 "s3:PutObjectTagging",],
        resources=["*"],
    ))
    suppress_cdk_nag_errors_by_grant_readwrite(lambda_role)

    with open(os.path.join(SCRIPT_DIRECTORY, "..", "stepfn", "process_edit", "object-tag-access-token.py")) as fd:
        code = fd.read()

    tag_fn = aws_lambda.Function(
        stack,
        id='ShotLocker-S3-Object-Tag',
        function_name='ShotLocker-S3-Object-Tag',
        description='Tag objects in S3',
        runtime=aws_lambda.Runtime.PYTHON_3_9,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(900),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=4096, # MB
    )
    return tag_fn


def _create_s3_object_tag_task(stack, tag_fn, postfix=""):
    tag_job = stepfn_tasks.LambdaInvoke(stack, 
        'ShotLocker-S3-Object-Tag-Task' + postfix,
        lambda_function=tag_fn,
        output_path="$.Payload",
    )
    return tag_job


def _create_find_processed_edit_function(stack, lambda_layers, environment):

    # lambda role
    lambda_role = iam.Role(stack, 'ShotLocker-Edit-Processed-Edit-Role', 
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
                 "s3:ListBucket"],
        resources=["*"],
    ))
    suppress_cdk_nag_errors_by_grant_readwrite(lambda_role)

    with open(os.path.join(SCRIPT_DIRECTORY, "..", "stepfn", "process_edit", "find-processed-edit.py")) as fd:
        code = fd.read()

    fn = aws_lambda.Function(
        stack,
        id='ShotLocker-Find-Processed-Edit',
        function_name='ShotLocker-Find-Processed-Edit', 
        description='Find Processed Edit in S3',
        runtime=aws_lambda.Runtime.PYTHON_3_9,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(15),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=128, # MB
    )
    return fn


def _create_find_processed_edit_task(stack, lambda_fn, postfix=""):
    job = stepfn_tasks.LambdaInvoke(stack, 
        "ShotLocker-Find-Processed-Edit-Task" + postfix,
        lambda_function=lambda_fn,
        output_path="$.Payload",
    )
    return job


def _create_remove_bucket_access_function(stack, lambda_layers, environment):

    # lambda role
    lambda_role = iam.Role(stack, 'ShotLocker-Edit-Remove-Bucket-Access-Role', 
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
                 "s3:ListAllMyBuckets",
                 "s3:ListBucket",
                 "s3:PutBucketTagging",
                 "s3:PutObject" ],
        resources=["*"],
    ))
    suppress_cdk_nag_errors_by_grant_readwrite(lambda_role)

    with open(os.path.join(SCRIPT_DIRECTORY, "..", "stepfn", "process_edit", "remove-bucket-access.py")) as fd:
        code = fd.read()

    fn = aws_lambda.Function(
        stack,
        id='ShotLocker-Remove-Bucket-Access',
        function_name='ShotLocker-Remove-Bucket-Access', 
        description='Remove Bucket Access',
        runtime=aws_lambda.Runtime.PYTHON_3_9,
        handler='index.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_inline(code),
        timeout=Duration.seconds(15),
        layers=lambda_layers,
        environment=environment,
        retry_attempts=0,
        memory_size=128, # MB
    )
    return fn


def _create_remove_bucket_access_task(stack, lambda_fn, postfix=""):
    job = stepfn_tasks.LambdaInvoke(stack, 
        "ShotLocker-Remove-Bucket-Access-Task" + postfix,
        lambda_function=lambda_fn,
        output_path="$.Payload",
    )
    return job
