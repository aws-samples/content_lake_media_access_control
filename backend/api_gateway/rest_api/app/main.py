# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import re
import boto3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_v1.api import router as api_router
from mangum import Mangum


def get_origins():
    origins = []

    try:
        # Amazon Cloudfront CDN domain
        ssm_client = boto3.client("ssm")
        response = ssm_client.get_parameter(Name=f"/ShotLocker/Config/CdnDomainUrl")
        origins.append(response['Parameter']['Value'])

        # optional domains
        opt = os.environ.get("CORS_ALLOW_ORIGINS_LIST")
        if opt:
            # regex to split string with delimiters: ; , [space]
            origins.extend(re.split('[;,\s]', opt))
    except:
        origins.append('*')

    return origins


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World!"}


app.include_router(api_router, prefix='/api')
handler = Mangum(app)
