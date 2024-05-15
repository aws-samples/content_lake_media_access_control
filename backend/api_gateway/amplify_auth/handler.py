# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
import boto3


def lambda_handler(event, context):

    auth = {
        "auth": {
            "userPoolId": os.environ.get('COGNITO_USER_POOL_ID'),
            "region": os.environ.get('AWS_REGION'),
            "userPoolWebClientId": os.environ.get('COGNITO_USER_POOL_CLIENT_ID'),
        }
    }

    ssm_client = boto3.client("ssm")

    response = ssm_client.get_parameter(Name=f"/ShotLocker/Config/CdnDomainUrl")
    cdn_domain_url = response['Parameter']['Value']

    response = ssm_client.get_parameter(Name=f"/ShotLocker/Config/CognitoDomainName")
    cognito_domain_name = response['Parameter']['Value']

    auth['auth']['oauth'] = {
        'domain': cognito_domain_name,
        'redirectSignIn': cdn_domain_url,
        'redirectSignOut': cdn_domain_url,
        'responseType': 'code',
        'scope': ['email', 'openid', 'profile', 'aws.cognito.signin.user.admin'],
    }
    
    return {
        "statusCode": 200,
        "body": json.dumps(auth)
    }

