# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from constructs import Construct
from aws_cdk import (
    CfnOutput,
    Stack,
    aws_logs as logs,
    aws_ssm as ssm,
    Tags,
)
import cdk_nag as nag
from . import (
    api_gateway,
    bucket_stepfn,
    cognito,
    edit_stepfn, 
    functions,
    lambda_layers,
    s3_buckets,
    website_cdn
)

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class ShotLockerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # user context settings
        self.setup_user_settings()

        # any postfix on naming
        self.postfix = '-' + self.user_settings['postfix'] if 'postfix' in self.user_settings else ""

        log_group = self.create_log_group()

        # Lambda Layers
        boto3_lambda_layer = lambda_layers.create_boto3_lambda_layer(self)
        otio_lambda_layer = lambda_layers.create_otio_lambda_layer(self)
        shotlocker_lambda_layer = lambda_layers.create_shotlocker_module_lambda_layer(self)
        lambda_layer = {
            'boto3': boto3_lambda_layer,
            'otio': otio_lambda_layer,
            'shotlocker': shotlocker_lambda_layer
        }
        lambda_layer_list = list(lambda_layer.values())

        # resources
        access_bucket = s3_buckets.create_access_log_bucket(self)

        user_pool, user_client, cognito_domain = cognito.create_cognito_user_pool(self)

        bucket_stepfns = bucket_stepfn.create_bucket_step_functions(self, lambda_layer_list, log_group)

        edit_stepfns = edit_stepfn.create_edit_step_functions(self, lambda_layer_list, log_group)

        api, api_resources = api_gateway.create_api_gateway(self, lambda_layer, user_pool, user_client, log_group, bucket_stepfns, edit_stepfns)

        upload = functions.create_upload_edit_function(self, lambda_layer_list, log_group, edit_stepfns['process_edit'])

        s3_bucket, cdn_dist = website_cdn.create_website_and_cdn(self, api_gateway_rest_api=api,
                                                                 access_log_bucket=access_bucket)

        cognito.set_cognito_client_callbacks(self, user_pool=user_pool, user_client=user_client, cdn_dist=cdn_dist,
                                             lambda_layers=[boto3_lambda_layer])

        self.write_parameter_store(cdn_dist, s3_bucket, cognito_domain, bucket_stepfns, edit_stepfns)

        # tag resources
        resources = [log_group, 
                     boto3_lambda_layer, otio_lambda_layer, shotlocker_lambda_layer, 
                     api, upload, user_pool, user_client, cognito_domain, 
                     s3_bucket, cdn_dist]
        resources.extend(bucket_stepfns.values())
        resources.extend(edit_stepfns.values())
        resources.extend(api_resources)
        for resource in resources:
            Tags.of(resource).add('Owner', 'ShotLocker')

        self.nag_suppression()

        CfnOutput(self,'ShotLocker-CloudFront-DomainName',
            value=cdn_dist.domain_name,
            description='The distribution Domain Name',
            export_name='ShotLocker-Cloudfront-DomainName',
        )

        CfnOutput(self,'ShotLocker-CloudFront-URL',
            value=f"https://{cdn_dist.domain_name}",
            description='The distribution URL',
            export_name='ShotLocker-Cloudfront-URL',
        )

        CfnOutput(self, 'ShotLocker-Website-BucketName', 
            value=s3_bucket.bucket_name,
            description='The name of the S3 bucket for website',
            export_name='ShotLocker-WebsiteBucketName',
        )

        CfnOutput(self, 'ShotLocker-APIGatewayURL', 
            value=api.url,
            description='The API Gateway URL',
            export_name='ShotLocker-APIGatewayURL',
        )

        CfnOutput(self, 'ShotLocker-Cognito-UserPoolId', 
            value=user_pool.user_pool_id,
            description='Cognito User Pool Id',
            export_name='ShotLocker-CognitoUserPoolId',
        )

        CfnOutput(self, 'ShotLocker-Cognito-ClientId', 
            value=user_client.user_pool_client_id,
            description='Cognito Client Id',
            export_name='ShotLocker-CognitoClientId',
        )

        CfnOutput(self, 'ShotLocker-LogGroupName', 
            value=log_group.log_group_name,
            description='CloudWatch Log Name',
            export_name='ShotLocker-LogGroupName',
        )

        CfnOutput(self, 'ShotLocker-Cognito-Domain', 
            value=cognito_domain.domain_name,
            description='Cognito Domain',
            export_name='ShotLocker-CognitoDomain',
        )

        CfnOutput(self, 'ShotLocker-AccessLog-BucketName', 
            value=access_bucket.bucket_name,
            description='The name of the S3 bucket for access logs',
            export_name='ShotLocker-AccessLog-BucketName',
        )


    def nag_suppression(self):
        nag.NagSuppressions.add_stack_suppressions(self, [
            {
                "id": "AwsSolutions-L1",
                "reason": "Lambdas using Python 3.9 because of third party module pip install"
            },
            {
                "id": "AwsSolutions-S1",
                "reason": "S3 buckets do not need access logging"
            },
        ])


    def setup_user_settings(self):
        config = self.node.try_get_context("config")
        self.user_settings = self.node.try_get_context(config)


    def create_log_group(self):
        log_group = logs.LogGroup(self, "ShotLocker-LogGroup", 
            #removal_policy=RemovalPolicy.DESTROY,
        )
        return log_group
    

    def write_parameter_store(
        self, 
        cdn_dist, 
        web_bucket, 
        cognito_domain, 
        bucket_stepfns, 
        edit_stepfns
    ):

        ssm.StringParameter(self, "ShotLockerConfigCdnDomainName",
            parameter_name="/ShotLocker/Config/CdnDomainName",
            description="CDN Domain Name",
            string_value=cdn_dist.domain_name
        )

        ssm.StringParameter(self, "ShotLockerConfigCdnDomainUrl",
            parameter_name="/ShotLocker/Config/CdnDomainUrl",
            description="CDN URL endpoint",
            string_value=f"https://{cdn_dist.domain_name}/"
        )

        ssm.StringParameter(self, "ShotLockerConfigWebsiteBucketName",
            parameter_name="/ShotLocker/Config/WebsiteBucketName",
            description="S3 bucket for website",
            string_value=web_bucket.bucket_name
        )

        ssm.StringParameter(self, "ShotLockerConfigCognitoDomainName",
            parameter_name="/ShotLocker/Config/CognitoDomainName",
            description="Cognito Domain",
            string_value=f'{cognito_domain.domain_name}.auth.{self.region}.amazoncognito.com'
        )

        ssm.StringParameter(self, "ShotLockerConfigBucketDisableArn",
            parameter_name="/ShotLocker/Config/BucketDisableArn",
            description="Bucket Disable Step Function Arn",
            string_value=bucket_stepfns['bucket_disable'].state_machine_arn
        )

        ssm.StringParameter(self, "ShotLockerConfigProcessEditArn",
            parameter_name="/ShotLocker/Config/ProcessEditArn",
            description="Process Edit Step Function Arn",
            string_value=edit_stepfns['process_edit'].state_machine_arn
        )

        ssm.StringParameter(self, "ShotLockerConfigAddEditAccessArn",
            parameter_name="/ShotLocker/Config/AddEditAccessArn",
            description="Add Edit Access Step Function Arn",
            string_value=edit_stepfns['add_access'].state_machine_arn
        )

        ssm.StringParameter(self, "ShotLockerConfigRemoveEditAccessArn",
            parameter_name="/ShotLocker/Config/RemoveEditAccessArn",
            description="Remove Edit Access Step Function Arn",
            string_value=edit_stepfns['remove_access'].state_machine_arn
        )

