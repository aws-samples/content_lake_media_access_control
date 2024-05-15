# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from typing import Any
import shotlocker
from shotlocker.log import log_entry
from shotlocker.cwprint import cwprint_exc
from fastapi import APIRouter, HTTPException, Depends
from app.validate.date import validate_date
from app.validate.iam import validate_iam_user_role_arn


router = APIRouter()

@router.get("/lockers/{locker}/edits/{edit}/access")
async def get_access(
    locker: str,
    edit: str,
) -> Any:
    if not shotlocker.bucket.is_shot_locker_bucket_valid(locker):
        raise HTTPException(
           status_code=404,
           detail="Shot Locker bucket not found"
        )

    if not shotlocker.edit.is_shot_locker_bucket_edit_valid(locker, edit):
        raise HTTPException(
           status_code=404,
           detail="Shot Locker edit not found"
        )

    policy = shotlocker.bucket_policy.get_shot_locker_bucket_policy_as_json(locker)
    if not policy:
        return {"access": []}

    try:
        user_access = shotlocker.bucket_policy.get_shot_locker_bucket_user_access_list(policy, edit,
                                                                                       include_expired_date=True)
    except:
        cwprint_exc()
        raise HTTPException(
           status_code=500,
           detail="Shot Locker get access failed"
        )


    return {"access": user_access}


@router.put("/lockers/{locker}/edits/{edit}/access/grant/{expiry_date}/{arn:path}")
async def grant_access(
    locker: str,
    edit: str,
    expiry_date: str,
    arn: str,
) -> Any:
    if not shotlocker.bucket.is_shot_locker_bucket_valid(locker):
        raise HTTPException(
           status_code=404,
           detail="Shot Locker bucket not found"
        )

    if not shotlocker.edit.is_shot_locker_bucket_edit_valid(locker, edit):
        raise HTTPException(
           status_code=404,
           detail="Shot Locker edit not found"
        )

    if not validate_iam_user_role_arn(arn):
        raise HTTPException(
           status_code=400,
           detail="IAM arn not valid"
        )

    if not validate_date(expiry_date):
        raise HTTPException(
           status_code=400,
           detail="Shot Locker expiry date not valid"
        )

    policy = shotlocker.bucket_policy.get_shot_locker_bucket_policy_as_json(locker)

    try:
        shotlocker.bucket_policy.add_user_to_shot_locker_bucket_policy(locker, policy, arn, edit, expired_date=expiry_date)
    except:
        cwprint_exc("grant_access()")
        raise HTTPException(
           status_code=400,
           detail="arn not valid"
        )

    log_entry(edit, f"Access granted to {arn}")

    return {"grant": f"grant {arn}"}


@router.put("/lockers/{locker}/edits/{edit}/access/deny/{arn:path}")
async def deny_access(
    locker: str,
    edit: str,
    arn: str,
) -> Any:
    if not shotlocker.bucket.is_shot_locker_bucket_valid(locker):
        raise HTTPException(
           status_code=404,
           detail="Shot Locker bucket not found"
        )

    if not shotlocker.edit.is_shot_locker_bucket_edit_valid(locker, edit):
        raise HTTPException(
           status_code=404,
           detail="Shot Locker edit not found"
        )

    if not validate_iam_user_role_arn(arn):
        raise HTTPException(
           status_code=400,
           detail="IAM arn not valid"
        )

    policy = shotlocker.bucket_policy.get_shot_locker_bucket_policy_as_json(locker)

    try:
        shotlocker.bucket_policy.remove_user_from_shot_locker_bucket_policy(locker, policy, arn, edit)
    except Exception as e:
        cwprint_exc()
        raise HTTPException(
           status_code=400,
           detail="arn not valid"
        )

    log_entry(edit, f"Access revoked for {arn}")

    return {"deny": f"deny {arn}"}
