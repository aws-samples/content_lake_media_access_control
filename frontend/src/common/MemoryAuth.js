// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

/// adapted from:
// https://marmelab.com/blog/2020/07/02/manage-your-jwt-react-admin-authentication-in-memory.html


const MemoryAuth = () => {

  let authJwtFn = null;

  const getAuthJwtFn = () => { return authJwtFn; }
  const setAuthJwtFn = (fn) => {
    authJwtFn = fn;
    return true;
  };
  const hasAuthJwtFn = () => authJwtFn !== null;

  const clear = () => {
    authJwtFn = null;
  }
  
  return {
    hasAuthJwtFn,
    getAuthJwtFn,
    setAuthJwtFn,
    clear
  }
};

export default MemoryAuth();

