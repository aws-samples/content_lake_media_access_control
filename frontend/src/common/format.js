// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

export const formatIsoDuration = isotime => {
  if (!isotime) {
    return "?";
  }
  isotime = isotime.replace("PT", "");
  isotime = isotime.replace("H", " hours");
  return isotime;  
};


export const formatIso8601 = iso8601 => {
  if (!iso8601) {
    return "?";
  }
  if (!iso8601.endsWith("Z")) {
    iso8601 += "Z";
  }

  var d = new Date(iso8601);
  return d.toLocaleString("en-US", {
    "dateStyle": "medium", 
    "hour12": false, 
    "timeStyle": "long"
  });
};

