# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from fastapi import APIRouter

from .endpoints import access
from .endpoints import edits
from .endpoints import lockers

router = APIRouter()
router.include_router(access.router)
router.include_router(edits.router)
router.include_router(lockers.router)

