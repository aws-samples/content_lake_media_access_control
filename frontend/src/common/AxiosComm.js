// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import axios from "axios";
import MemoryAuth from "./MemoryAuth";
import { Auth } from 'aws-amplify';


const axiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL + "/api",
  timeout: 15000,
  headers: {
      'Content-Type': 'application/json',
      'accept': 'application/json'
  }
});

axiosInstance.interceptors.request.use(async (config) => {
  if (MemoryAuth.hasAuthJwtFn())
  {
      let fn = MemoryAuth.getAuthJwtFn();
      let jwt = await fn()
      if (jwt) {
        config.headers["Authorization"] = "Bearer " + jwt;
      }
  }
  return config;
},
(error) => {
  Promise.reject(error);
});

/**
 * Catch the UnAuthorized Request
 */
axiosInstance.interceptors.response.use((response) => response, (error) => {
  if (error.response.status === 401) {
    MemoryAuth.clear();
    Auth.signOut();
  }
});

export default axiosInstance;
