# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import urllib
import collections
import opentimelineio as otio


def has_media_reference(clip, *, include_missing_ref=False):
    return (isinstance(clip.media_reference, otio.schema.ExternalReference) or
            (include_missing_ref and isinstance(clip.media_reference, otio.schema.MissingReference)))


def is_media_reference_mssing(clip):
    return isinstance(clip.media_reference, otio.schema.MissingReference)


def find_media_url_in_clip(clip, *, include_missing_ref=False):
    url = None
    if isinstance(clip.media_reference, otio.schema.ExternalReference):
        url = clip.media_reference.target_url
    elif include_missing_ref and isinstance(clip.media_reference, otio.schema.MissingReference):
        # see if in metadata (Resolve puts media urls in the metadata)
        try:
            metadata = clip.media_reference.metadata
        except:
            metadata = {}

        for k,v in metadata.items():
            if k == 'Media Url':
                url = v
            elif isinstance(v, collections.abc.Mapping):
                if 'Media Url' in v:
                    url = v['Media Url']

    if url:
        url = urllib.parse.unquote_plus(url, encoding='utf-8')

    return url 
