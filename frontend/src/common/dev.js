// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

export const isDevelopment = () => {
  return !!process.env.REACT_APP_API_URL;
};
