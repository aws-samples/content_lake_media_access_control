
from aws_cdk import (
    aws_iam as iam,
)
import cdk_nag as nag


def require_tls_add_to_resource_policy(bucket):
    bucket.add_to_resource_policy(
        iam.PolicyStatement(
            effect = iam.Effect.DENY,
            principals = [iam.AnyPrincipal()],
            actions = ["s3:*"],
            resources = [f'{bucket.bucket_arn}/*', bucket.bucket_arn],
            conditions = {
                'Bool': { "aws:SecureTransport": "false" },
            },
        )
    )


def suppress_cdk_nag_errors_by_grant_readwrite(scope, resource_type:str='lambda'):

    reason = f"This {resource_type} owns the data in this bucket and should have full access to control its assets."

    nag.NagSuppressions.add_resource_suppressions(
        scope,
        [
            {
                'id': "AwsSolutions-IAM5",
                'reason': reason,
                'appliesTo': [
                    {
                        'regex': "/Action::s3:.*/g",
                    },
                ],
            },
            {
                'id': "AwsSolutions-IAM5",
                'reason': reason,
                'appliesTo': [
                    {
                        # https://github.com/cdklabs/cdk-nag#suppressing-a-rule
                        'regex': "/^Resource::.*/g",
                    },
                ],
            },
        ],
        True
    )
