# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from .cdk_lambda_layer_builder.constructs import BuildPyLayerAsset
from aws_cdk import (
    aws_lambda,
)

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def create_boto3_lambda_layer(stack) -> aws_lambda.LayerVersion:
    """ Create lambda layer with the latest Python boto3 module """

    # create the pipy layer
    layer_asset = BuildPyLayerAsset.from_pypi(stack, 'ShotLocker-boto3-Layer-Asset',
        pypi_requirements=['boto3', 'crhelper'],
        py_runtime=aws_lambda.Runtime.PYTHON_3_9,
    )
    layer = aws_lambda.LayerVersion(
        stack,
        id='ShotLocker-boto3-Layer',
        layer_version_name='ShotLocker-boto3-Layer',
        code=aws_lambda.Code.from_bucket(layer_asset.asset_bucket, layer_asset.asset_key),
        compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_9],
        compatible_architectures=[aws_lambda.Architecture.X86_64],
        description ='AWS Boto3 Python module'
    )
    return layer


def create_otio_lambda_layer(stack) -> aws_lambda.LayerVersion:

    # OpenTimelineIO has a C++ binary as part of the module

    # create the pipy layer
    layer_asset = BuildPyLayerAsset.from_pypi(stack, 'ShotLocker-OTIO-Layer-Asset',
        pypi_requirements=['OpenTimelineIO==0.16.0', 'OpenTimelineIO-Plugins==0.16.0'],
        py_runtime=aws_lambda.Runtime.PYTHON_3_9,
    )

    layer = aws_lambda.LayerVersion(
        stack,
        id='ShotLocker-OTIO-Layer',
        layer_version_name='ShotLocker-OTIO-Layer',
        code=aws_lambda.Code.from_bucket(layer_asset.asset_bucket, layer_asset.asset_key),
        compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_9],
        compatible_architectures=[aws_lambda.Architecture.X86_64],
        description ='OpenTimelineIO Python modules'
    )
    return layer


def create_shotlocker_module_lambda_layer(stack) -> aws_lambda.LayerVersion:
    module_layer_asset = BuildPyLayerAsset.from_modules(stack, 'ShotLocker-Module-LayerAsset',
        local_module_dirs=[os.path.join(SCRIPT_DIRECTORY, '..', 'core', 'shotlocker')],
        py_runtime=aws_lambda.Runtime.PYTHON_3_9,
    )
    module_layer = aws_lambda.LayerVersion(
        stack,
        id='Shotlocker-Module-Layer',
        layer_version_name='Shotlocker-Module-Layer',
        code=aws_lambda.Code.from_bucket(module_layer_asset.asset_bucket, module_layer_asset.asset_key),
        compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_9],
        description ='ShotLocker custom Python module'
    )
    return module_layer
