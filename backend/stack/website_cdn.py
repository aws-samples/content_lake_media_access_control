# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from aws_cdk import (
    Duration,
    aws_cloudfront as cdn,
    aws_cloudfront_origins as cdn_origins,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3_deploy,
    RemovalPolicy,
)
import cdk_nag as nag
from .security import (
    require_tls_add_to_resource_policy, 
    suppress_cdk_nag_errors_by_grant_readwrite
)


SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def create_website_and_cdn(
    stack, 
    *, 
    api_gateway_rest_api=None,
    access_log_bucket=None,
):
    # React website build location
    website_dir = os.path.join(SCRIPT_DIRECTORY, '..', '..', 'frontend', 'build')

    hosting_bucket = s3.Bucket(stack, 'ShotLocker-Frontend-Bucket', 
        auto_delete_objects=True,
        block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        removal_policy=RemovalPolicy.DESTROY,
    )

    require_tls_add_to_resource_policy(hosting_bucket)

    distribution = cdn.Distribution(stack, 'ShotLocker-Cloudfront-Distribution', 
        default_root_object='index.html',
        minimum_protocol_version=cdn.SecurityPolicyProtocol.TLS_V1_2_2019,
        error_responses=[
            cdn.ErrorResponse(
                http_status=403,
                response_http_status=200,
                response_page_path='/index.html',
            ),
            cdn.ErrorResponse(
                http_status=404,
                response_http_status=200,
                response_page_path='/index.html',
            ),
        ],
        enable_logging=True,
        log_bucket=access_log_bucket,
        log_file_prefix="cloudfront-distribution-access-logs/",
        log_includes_cookies=True,
        default_behavior=cdn.BehaviorOptions(
            origin=cdn_origins.S3Origin(hosting_bucket),
            viewer_protocol_policy=cdn.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        ),
        additional_behaviors={
            '/api/*': cdn.BehaviorOptions(
                origin=cdn_origins.RestApiOrigin(api_gateway_rest_api),
                allowed_methods=cdn.AllowedMethods.ALLOW_ALL,
                viewer_protocol_policy=cdn.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                compress=False,
                cache_policy=cdn.CachePolicy(stack, 'ShotLocker-RestApiCachePolicy',
                    header_behavior=cdn.CacheHeaderBehavior.allow_list('Authorization', 'Origin', 'Referer'),
                    query_string_behavior=cdn.CacheQueryStringBehavior.all(),
                    cache_policy_name='ShotLocker-ApiGwWithAuthorization',
                    cookie_behavior=cdn.CacheCookieBehavior.all(),
                    enable_accept_encoding_brotli=True,
                    enable_accept_encoding_gzip=True,
                    # see https://github.com/aws/aws-cdk/issues/16977 
                    #  - we need to set the maxTtl to the smallest possible value
                    max_ttl=Duration.seconds(1),
                    min_ttl=Duration.seconds(0),
                    default_ttl=Duration.seconds(0)
                ),
                origin_request_policy=cdn.OriginRequestPolicy(stack, 'ShotLocker-RestApiOriginRequestPolicy', 
                    header_behavior=cdn.OriginRequestHeaderBehavior.none(), # allow_list('Origin', 'Referer'),
                    query_string_behavior=cdn.OriginRequestQueryStringBehavior.all(),
                    cookie_behavior=cdn.OriginRequestCookieBehavior.none(),
                    origin_request_policy_name='ShotLocker-ApiGwWithAuthorization',
                )
            )
        },
    )

    nag.NagSuppressions.add_resource_suppressions(distribution, [
        {
            "id": "AwsSolutions-CFR1",
            "reason": "No need for Geo restrictions"
        },
        {
            "id": "AwsSolutions-CFR2",
            "reason": "Not associated with WAF"
        },
        {
            "id": "AwsSolutions-CFR4",
            "reason": "Using the default CloudFront viewer certificate"
        },
    ], True)


    # role for bucket deployment
    deploy_role = iam.Role(stack, 'ShotLocker-Bucket-Deployment-Role', 
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    deploy_role.add_to_policy(iam.PolicyStatement(
        actions=["s3:AbortMultipartUpload", 
                 "s3:DeleteObject",
                 "s3:GetBucketLocation",
                 "s3:GetObject",
                 "s3:ListAllMyBuckets",
                 "s3:ListBucket",
                 "s3:ListBucketMultipartUpload",
                 "s3:ListMultipartUploadParts",
                 "s3:PutObject", ],
        resources=["*"],
    ))
    suppress_cdk_nag_errors_by_grant_readwrite(deploy_role)

    bucket_deployment = s3_deploy.BucketDeployment(stack, 'ShotLocker-Bucket-Deployment',
        sources=[s3_deploy.Source.asset(website_dir)],
        destination_bucket=hosting_bucket,
        distribution=distribution,
        distribution_paths=['/*'],
        role=deploy_role
    )

    return hosting_bucket, distribution
