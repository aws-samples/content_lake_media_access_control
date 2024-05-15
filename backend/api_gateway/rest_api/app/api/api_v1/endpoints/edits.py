# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from typing import Any, Optional
import shotlocker
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from fastapi.responses import FileResponse, StreamingResponse


router = APIRouter()

@router.get("/lockers/{locker}/edits")
async def get_edits(
    locker: str,
    all: Optional[bool] = Query(False, description="list active and inactive edits"),
) -> Any:
    if not shotlocker.bucket.is_shot_locker_bucket_valid(locker):
        raise HTTPException(
           status_code=404,
           detail="Shot Locker bucket not found"
        )

    edits = shotlocker.edit.get_shot_locker_bucket_edit_detailed_list(locker, include_inactive=all)

    return {"edit": edits}


@router.get("/lockers/{locker}/edits/{edit}")
async def get_edit(
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

    edit = shotlocker.edit.get_shot_locker_bucket_edit_info(locker, edit)

    return edit


# example upload
# curl -L -F "file=@/Users/pxpalmer/Downloads/Fathead_SIGGRAPH2022_FCP_7_XML_V5.xml" http://localhost:8080/api/v1/lockers/contentlake-fathead/edits

@router.post("/lockers/{locker}/edits")
async def create_edit(
    locker: str,
    file: UploadFile = File(...),
) -> Any:

    if not shotlocker.bucket.is_shot_locker_bucket_valid(locker):
        raise HTTPException(
           status_code=404,
           detail="Shot Locker bucket not found"
        )

    file.file.seek(0,2)
    length = file.file.tell()
    file.file.seek(0)

    if length > 20000000:
        raise HTTPException(
            status_code=413,
            detail="Media too large"
        )

    body = file.file.read()

    upload_key = shotlocker.edit.upload_new_edit(locker, file.filename, body)

    return {"upload": upload_key }
    

@router.get("/lockers/{locker}/edits/{edit}/logs")
async def get_edit_logs(    
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
        
    logs = shotlocker.log.get_log_entries(edit)
    
    return { 'log': logs }


@router.put("/lockers/{locker}/edits/{edit}/enable")
async def enable_locker(    
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

    if not shotlocker.edit.set_shot_locker_bucket_edit(locker, edit, enable=True):
        raise HTTPException(
           status_code=500,
           detail="Shot Locker edit unable to enable"
        )
    
    shotlocker.log.log_entry(edit, f"Edit ({edit}) is enabled")

    edit = shotlocker.edit.get_shot_locker_bucket_edit_info(locker, edit)
    return {"edit": edit}


@router.put("/lockers/{locker}/edits/{edit}/disable")
async def disable_locker(    
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

    if not shotlocker.edit.set_shot_locker_bucket_edit(locker, edit, enable=False):
        raise HTTPException(
           status_code=500,
           detail="Shot Locker edit unable to disable"
        )

    shotlocker.log.log_entry(edit, f"Edit ({edit}) is disabled")

    edit = shotlocker.edit.get_shot_locker_bucket_edit_info(locker, edit)
    return {"edit": edit}
