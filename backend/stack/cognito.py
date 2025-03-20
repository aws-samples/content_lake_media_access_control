# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from aws_cdk import (
    Duration,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_lambda,
    custom_resources as cr,
    CustomResource,
    RemovalPolicy,
)
import cdk_nag as nag
from .security import suppress_cdk_nag_errors_by_grant_readwrite


SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def create_cognito_user_pool(stack, *, mfa_required=False):
    user_pool = cognito.UserPool(stack, "ShotLocker-Cognito-UserPool", 
        user_pool_name='ShotLocker-Cognito-UserPool',
        removal_policy=RemovalPolicy.DESTROY,
        mfa=cognito.Mfa.REQUIRED if mfa_required else cognito.Mfa.OFF,
        mfa_second_factor=cognito.MfaSecondFactor(
            otp=True,
            sms=False,
        ),
        password_policy=cognito.PasswordPolicy(
            min_length=8,
            require_digits=True,
            require_lowercase=True,
            require_symbols=True,
            require_uppercase=True,
        ),
    )

    domain_prefix = "shotlocker" + stack.postfix.lower()
    domain = user_pool.add_domain("ShotLocker-CognitoDomain",
        cognito_domain=cognito.CognitoDomainOptions(domain_prefix=domain_prefix)
    )

    client = user_pool.add_client("ShotLocker-WebClient", 
        user_pool_client_name="ShotLocker-WebClient",
        id_token_validity=Duration.days(1),
        access_token_validity=Duration.days(1),
        auth_flows=cognito.AuthFlow(
            user_password=True,
            user_srp=True,
            custom=True,
        ),
    )

    nag.NagSuppressions.add_resource_suppressions(user_pool, [
        {
            "id": "AwsSolutions-COG2",
            "reason": "user setting"
        },
        {
            "id": "AwsSolutions-COG3",
            "reason": "deprecated"
        },
    ])

    return user_pool, client, domain


def set_cognito_client_callbacks(
    stack,
    *,
    user_pool=None,
    user_client=None,
    cdn_dist=None,
    lambda_layers=None
):
    if not lambda_layers:
        lambda_layers = []

    set_callback_lambda = aws_lambda.Function(
        stack,
        "ShotLocker-Cognito-Client-CallbackEventHandler",
        environment={
            "CLOUDFRONT_DISTRIBUTION_DOMAIN_URL": f"https://{cdn_dist.domain_name}/",
            "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
            "COGNITO_USER_POOL_CLIENT_ID": user_client.user_pool_client_id,
        },
        runtime=aws_lambda.Runtime.PYTHON_3_9,
        layers=lambda_layers,
        handler="cognito_hosted_callback.handler",
        code=aws_lambda.Code.from_asset(os.path.join(SCRIPT_DIRECTORY, "cdk_custom_resource", "cognito_hosted_callback")),
    )

    set_callback_lambda.add_to_role_policy(
        statement=iam.PolicyStatement(
            actions=[
                "cognito-idp:DescribeUserPoolClient",
                "cognito-idp:UpdateUserPoolClient",
            ],
            effect=iam.Effect.ALLOW,
            resources=[user_pool.user_pool_arn],
        )
    )
    set_callback_lambda.add_to_role_policy(iam.PolicyStatement(
      actions=["events:PutRule"],
      resources=["*"],
    ))

    lambda_role = iam.Role(
        stack, 
        'ShotLocker-Cognito-Client', 
        managed_policies=[
            iam.ManagedPolicy.from_aws_managed_policy_name(
                managed_policy_name="AWSLambdaExecute"
            )
        ],
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )

    provider = cr.Provider(
        stack,
        "ShotLocker-CognitoCallbackProvider",
        on_event_handler=set_callback_lambda,
        role=lambda_role,
    )

    CustomResource(
        stack,
        "ShotLocker-CustomResourceToConfigCallback",
        service_token=provider.service_token,
    )

    suppress_cdk_nag_errors_by_grant_readwrite(set_callback_lambda)
    suppress_cdk_nag_errors_by_grant_readwrite(lambda_role)

    nag.NagSuppressions.add_resource_suppressions(lambda_role, [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "Uses AWS managed role for cloud watch logs"
        },
    ], True)
    nag.NagSuppressions.add_resource_suppressions(set_callback_lambda, [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "Uses AWS managed role for cloud watch logs"
        },
    ], True)

