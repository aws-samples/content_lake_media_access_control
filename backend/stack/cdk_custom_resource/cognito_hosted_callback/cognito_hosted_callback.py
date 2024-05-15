# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import logging
from crhelper import CfnResource
import boto3

logger = logging.getLogger(__name__)

helper = CfnResource(
    json_logging=False,
    log_level="DEBUG",
    boto_level="CRITICAL",
    sleep_on_delete=120,
    ssl_verify=None,
)
cognito_client = boto3.client("cognito-idp")


def set_cognito_client_callbacks():
    try:
        domain_url = os.environ.get('CLOUDFRONT_DISTRIBUTION_DOMAIN_URL')
        user_pool_id = os.environ.get("COGNITO_USER_POOL_ID")
        user_pool_client_id = os.environ.get("COGNITO_USER_POOL_CLIENT_ID")

        client = cognito_client.describe_user_pool_client(UserPoolId=user_pool_id, ClientId=user_pool_client_id)

        kwargs = client['UserPoolClient']

        if 'CallbackURLs' not in kwargs:
            kwargs['CallbackURLs'] = []
        kwargs['CallbackURLs'].append(domain_url)

        # remove example url
        example = "https://example.com" 
        if example in kwargs['CallbackURLs']:
            kwargs['CallbackURLs'].remove(example)

        if 'LogoutURLs' not in kwargs:
            kwargs['LogoutURLs'] = []
        kwargs['LogoutURLs'].append(domain_url)

        # remove Read Only fields
        del(kwargs['LastModifiedDate'])
        del(kwargs['CreationDate'])

        rep = cognito_client.update_user_pool_client(**kwargs)
    except Exception as e:
        logger.exception(e)
        raise ValueError(
            "An error occurred when attempting to set the callback urls for the user pool client. See the CloudWatch logs for details"
        )


@helper.create
def create(event, context):
    logger.info("Got Create")
    set_cognito_client_callbacks()
    return None


@helper.update
def update(event, context):
    logger.info("Got Update")
    set_cognito_client_callbacks()
    return None


# Delete never returns anything.
# Should not fail if the underlying resources are already deleted.
@helper.delete
def delete(event, context):
    logger.info("Got Delete")


@helper.poll_create
def poll_create(event, context):
    logger.info("Got create poll")
    # Return a resource id or True to indicate that creation is complete.
    # If True is returned an id will be generated
    return True


def handler(event, context):
    helper(event, context)


