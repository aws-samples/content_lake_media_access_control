# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from aws_cdk import (
    Duration,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_lambda,
    RemovalPolicy,
)
import cdk_nag as nag
from .cdk_lambda_layer_builder.constructs import BuildPyLayerAsset

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def create_fastapi_uvicorn_mangum_layer(stack) -> aws_lambda.LayerVersion:

    # create the pipy layer
    layer_asset = BuildPyLayerAsset.from_pypi(stack, 'ShotLocker-FastAPI-Uvicorn-Mangum-Layer-Asset',
        pypi_requirements=[
            'fastapi==0.105.0', 
            'uvicorn==0.24.0.post1', 
            'mangum==0.17.0', 
            'python-multipart==0.0.6', 
            'python-dotenv==1.0.0',
            'pydantic-settings==2.0.2',
            'requests==2.29.0',  # botocore does not support urllib3 v2, use older requests lib
        ],
        py_runtime=aws_lambda.Runtime.PYTHON_3_9,
        #platform="linux/amd64"
    )
    layer = aws_lambda.LayerVersion(
        stack,
        id='ShotLocker-FastAPI-Uvicorn-Mangum-Layer',
        code=aws_lambda.Code.from_bucket(layer_asset.asset_bucket, layer_asset.asset_key),
        compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_9],
        compatible_architectures=[aws_lambda.Architecture.X86_64],
        description ='FastAPI Python modules'
    )
    return layer


def create_rest_api_lambda(
    stack, 
    lambda_layers, 
    user_pool, 
    user_client, 
    log_group,
    bucket_stepfns,
    edit_stepfns,
):
    lambda_role = iam.Role(stack, 'ShotLocker-API-Gateway-ReST-Role', 
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["logs:CreateLogGroup", 
               "logs:CreateLogStream", 
               "logs:FilterLogEvents", 
               "logs:GetLogEvents",
               "logs:PutLogEvents"],
      resources=[f"arn:{stack.partition}:logs:*:*:*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["s3:DeleteBucketPolicy",
               "s3:GetBucketTagging",
               "s3:GetBucketLocation",
               "s3:GetBucketNotification",
               "s3:GetBucketPolicy",
               "s3:GetObjectTagging",
               "s3:ListAllMyBuckets",
               "s3:ListBucket",
               "s3:PutBucketNotification",
               "s3:PutBucketPolicy",
               "s3:PutBucketTagging",
               "s3:PutObject",
               "s3:PutObjectTagging"],
      resources=[f"arn:{stack.partition}:s3:::*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["iam:ListRoles", "iam:PassRole"],
      resources=["*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["states:DescribeExecution",],
      resources=["*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["states:StartExecution",],
      resources=[
          bucket_stepfns['bucket_disable'].state_machine_arn,
          edit_stepfns['add_access'].state_machine_arn,
          edit_stepfns['remove_access'].state_machine_arn,
      ],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["ssm:GetParameter",],
      resources=["*"],
    ))

    nag.NagSuppressions.add_resource_suppressions(
        lambda_role,
        [
            {
                'id': "AwsSolutions-IAM5",
                'reason': ','.join(["Lambda should be able to log", 
                           "able to list lambda functions",
                           "start and describe step functions",
                           "schedule tasks",
                           "read from the SSM Parameter store"]),
                'applies_to': [ "Resource::*" ]
            },
        ], True
    )

    fastapi_layer = create_fastapi_uvicorn_mangum_layer(stack)

    environment = {
        "AWS_PARTITION": stack.partition,
        "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
        "COGNITO_USER_POOL_CLIENT_ID": user_client.user_pool_client_id,
        "LOG_GROUP_NAME": log_group.log_group_name,
        "BUCKET_DISABLE_STEPFN_ARN": bucket_stepfns['bucket_disable'].state_machine_arn,
        "EDIT_ADD_ACCESS_STEPFN_ARN": edit_stepfns['add_access'].state_machine_arn,
        "EDIT_REMOVE_ACCESS_STEPFN_ARN": edit_stepfns['remove_access'].state_machine_arn,
    }

    layers = [fastapi_layer]
    layers.extend(list(lambda_layers.values()))

    api_fn = aws_lambda.Function(
        stack,
        id='ShotLocker-ReST-API',
        function_name='ShotLocker-ReST-API',
        description='Shot Locker ReST API',
        runtime=aws_lambda.Runtime.PYTHON_3_9,
        handler='app.main.handler',
        role=lambda_role,
        code=aws_lambda.Code.from_asset(os.path.join(SCRIPT_DIRECTORY, '..', 'api_gateway', 'rest_api')),
        timeout=Duration.seconds(120),
        layers=layers,
        retry_attempts=0,
        memory_size=2048, # MB
        environment=environment,
        tracing=aws_lambda.Tracing.PASS_THROUGH
    )

    return api_fn, lambda_role, fastapi_layer


def create_auth_lambda(
    stack, 
    lambda_layers, 
    user_pool, 
    user_client, 
):
    lambda_role = iam.Role(stack, 'ShotLocker-API-Gateway-Auth-Role', 
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["logs:CreateLogGroup", 
               "logs:CreateLogStream", 
               "logs:FilterLogEvents", 
               "logs:GetLogEvents",
               "logs:PutLogEvents"],
      resources=[f"arn:{stack.partition}:logs:*:*:*"],
    ))
    lambda_role.add_to_policy(iam.PolicyStatement(
      actions=["ssm:GetParameter",],
      resources=["*"],
    ))

    nag.NagSuppressions.add_resource_suppressions(
        lambda_role,
        [
            {
                'id': "AwsSolutions-IAM5",
                'reason': ','.join(["Lambda should be able to log", 
                           "able to list lambda functions",
                           "start and describe step functions",
                           "schedule tasks",
                           "read from the SSM Parameter store"]),
                'applies_to': [ "Resource::*" ]
            },
        ], True
    )

    environment = {
        "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
        "COGNITO_USER_POOL_CLIENT_ID": user_client.user_pool_client_id,
    }

    api_fn = aws_lambda.Function(
        stack,
        id='ShotLocker-API-Gateway-Auth',
        function_name='ShotLocker-API-Gateway-Auth',
        description='Shot Locker Auth Structure',
        runtime=aws_lambda.Runtime.PYTHON_3_9,
        handler='handler.lambda_handler',
        role=lambda_role,
        code=aws_lambda.Code.from_asset(os.path.join(SCRIPT_DIRECTORY, '..', 'api_gateway', 'amplify_auth')),
        timeout=Duration.seconds(12),
        layers=[lambda_layers['boto3']],
        retry_attempts=0,
        memory_size=128, # MB
        environment=environment,
        tracing=aws_lambda.Tracing.PASS_THROUGH
    )

    return api_fn, lambda_role


def create_api_gateway(
    stack, 
    lambda_layers, 
    user_pool, 
    user_client, 
    log_group,
    bucket_stepfns,
    edit_stepfns,
):
    
    rest_api_fn, rest_lambda_role, fastapi_layer = create_rest_api_lambda(
        stack, 
        lambda_layers, 
        user_pool, 
        user_client, 
        log_group,
        bucket_stepfns,
        edit_stepfns,
    )

    auth_api_fn, auth_lambda_role = create_auth_lambda(stack, lambda_layers, user_pool, user_client)

    authorizer = apigw.CognitoUserPoolsAuthorizer(stack, 
        "Authorizer", 
        cognito_user_pools=[user_pool],
    )

    api = apigw.RestApi(stack, 
        'ShotLocker-API-Gateway-ReST', 
        rest_api_name='ShotLocker-API-Gateway-ReST',
        default_cors_preflight_options=apigw.CorsOptions(
            allow_origins=apigw.Cors.ALL_ORIGINS,
            allow_credentials=True,
        ),
        deploy_options=apigw.StageOptions(
            logging_level=apigw.MethodLoggingLevel.INFO,
            data_trace_enabled=True,
            tracing_enabled=True,
            access_log_destination=apigw.LogGroupLogDestination(log_group),
        ),
        cloud_watch_role=True,
        cloud_watch_role_removal_policy=RemovalPolicy.DESTROY,
        description='Shot Locker API Gateway ReST Endpoint',
        endpoint_export_name='ShotLocker-API-Gateway-ReST'
    )

    resource = api.root.add_resource("api")

    # /api/auth
    auth_route = resource.add_resource("auth")
    auth_api_integration = apigw.LambdaIntegration(auth_api_fn)
    auth_method = auth_route.add_method("GET", auth_api_integration)

    # /api/{proxy+} 
    rest_api_integration = apigw.LambdaIntegration(rest_api_fn)
    proxy = resource.add_proxy(
       default_integration=rest_api_integration,
       any_method=True,
       default_method_options=apigw.MethodOptions(
           authorization_type=apigw.AuthorizationType.COGNITO,
           authorizer=authorizer
       )
    )

    nag.NagSuppressions.add_resource_suppressions(api, [
        {
            'id': 'AwsSolutions-APIG2',
            'reason': 'FastAPI for request validation'
        },
        {
            'id': 'AwsSolutions-APIG3',
            'reason': 'Not associated with WAF'
        },
        {
            "id": "AwsSolutions-APIG4",
            "reason": "Authentication done with API Gateway"
        },
        {
            "id": "AwsSolutions-IAM4",
            "reason": "API Gateway uses AWS managed role for cloud watch"
        },
    ], True)
    nag.NagSuppressions.add_stack_suppressions(stack, [
        {
            "id": "AwsSolutions-COG4",
            "reason": "Authentication done with API Gateway and Amplify"
        },
    ])

    resources = [rest_api_fn, rest_lambda_role, fastapi_layer, auth_api_fn, auth_lambda_role]

    return api, resources
