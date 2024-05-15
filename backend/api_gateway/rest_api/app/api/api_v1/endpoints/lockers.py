# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from typing import Any, Optional
import shotlocker
from fastapi import APIRouter, HTTPException, Query


router = APIRouter()

@router.get("/lockers")
async def get_lockers(
    available: Optional[bool] = Query(False, description="list buckets available to become a locker"),
    all: Optional[bool] = Query(False, description="list active and inactive lockers"),
) -> Any:
    if available:
        # list buckets available to be ShotLocker but are not
        buckets = shotlocker.bucket.get_shot_locker_available_bucket_list()
    else:
        # list buckets marked as ShotLocker buckets
        buckets = shotlocker.bucket.get_shot_locker_bucket_list(include_inactive=all)

    lockers = []
    for b in buckets:
        lockers.append({
            'name': b['name'],
            'active': b['active'],
        })

    return {"locker": lockers}


@router.get("/lockers/{locker}")
async def get_locker(    
    locker: str,
) -> Any:
    buckets = (shotlocker.bucket.get_shot_locker_bucket_list() +
               shotlocker.bucket.get_shot_locker_available_bucket_list())

    locker_info = None
    for b in buckets:
        if b['name'] == locker:
            locker_info = {
                'name': b['name'],
                'active': b['active'],
            }

    if not locker_info:
        raise HTTPException(
           status_code=404,
           detail="Bucket not found"
        )
    
    return {"locker": locker_info}


@router.put("/lockers/{locker}/enable")
async def enable_locker(    
    locker: str,
) -> Any:
    buckets = shotlocker.bucket.get_shot_locker_available_bucket_list()

    locker_info = None
    for b in buckets:
        if b['name'] == locker:
            locker_info = {
                'name': b['name'],
                'active': True
            }

    if not locker_info:
        raise HTTPException(
           status_code=404,
           detail="Bucket not found"
        )

    if not shotlocker.bucket.set_shot_locker_bucket(locker, enable=True):
        raise HTTPException(
           status_code=500,
           detail="Bucket not disabled"
        )

    return {"locker": locker_info}


@router.put("/lockers/{locker}/disable")
async def disable_locker(    
    locker: str,
) -> Any:
    buckets = shotlocker.bucket.get_shot_locker_bucket_list()

    locker_info = None
    for b in buckets:
        if b['name'] == locker:
            locker_info = {
                'name': b['name'],
                'active': False
            }

    if not locker_info:
        raise HTTPException(
           status_code=404,
           detail="Bucket not found"
        )

    if not shotlocker.bucket.set_shot_locker_bucket(locker, enable=False):
        raise HTTPException(
           status_code=500,
           detail="Bucket not disabled"
        )

    return {"locker": locker_info}

