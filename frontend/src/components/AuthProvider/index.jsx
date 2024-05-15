// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useEffect } from 'react';
import axiosInstance from '../../common/AxiosComm';
import { Spinner } from '@cloudscape-design/components';
import MemoryAuth from '../../common/MemoryAuth';
import { Amplify, Hub } from 'aws-amplify';
import { Authenticator } from '@aws-amplify/ui-react';
import Auth from '@aws-amplify/auth';
import '@aws-amplify/ui-react/styles.css';
import { isDevelopment } from '../../common/dev';

function AuthProvider({ children }) {
  
  const [loading, setLoading] = useState(true);
  const [ampConfigured, setAmpConfigured] = useState(false);

  const registerJwtCallback = () => {
    MemoryAuth.setAuthJwtFn(async () => {
      // Auth.currentSession() checks if token is expired and 
      // refreshes with Cognito if needed automatically
      try {
        const session = await Auth.currentSession();
        return session.getIdToken().getJwtToken();
      } catch (error) {
        return "";
      }
    });
  };
  const listener = (data) => {

    switch (data.payload.event) {
      case 'configured':
        console.log('amplify configured');
        registerJwtCallback();
        break;
      case 'signIn' || 'autoSignIn' || 'tokenRefresh':
        console.log('user signed in');
        registerJwtCallback();
        break;
      case 'signOut':
        console.log('user signed out');
        MemoryAuth.clear();
        break;
      default:
        console.log('amplify: ' + data.payload.event);
        break;
    }
  }
  Hub.listen('auth', listener);

  const checkAuthentication = async (auth) => {
    if ("oauth" in auth) {
      // Checks if there is a user currently authenticated, 
      // if not redirects to HOSTED UI where federation is enabled.
      try {
        await Auth.currentAuthenticatedUser();
      } catch (error) {
        await Auth.federatedSignIn();
      }
    }
  };

  useEffect(() => { 
    setLoading(true);
    axiosInstance.get("/auth")
      .then(response => {
        if (response && response.data) {

          if (isDevelopment()) {
            // if dev environment with local server, rewrite the oauth redirect
            if ("oauth" in response.data.auth) {
              response.data.auth.oauth.redirectSignIn = "http://localhost:3000";
              response.data.auth.oauth.redirectSignOut = "http://localhost:3000";
            }
          }

          Amplify.configure({ Auth: response.data.auth});

          checkAuthentication(response.data.auth);
        }
        setAmpConfigured(true);
        setLoading(false);
      })
      .catch(error => {
        console.log(error);
        alert("Shot Locker: Fatal Error unable to get auth provider information from server. This can occur if there is an issue with the installation or the configuration has changed. Please ask your administrator to check the logs.");
      });
  }, [ampConfigured]);

  return (
    <div>
    {loading ? <Spinner/> :
      <Authenticator hideSignUp={true}>
        <Authenticator.Provider>
          {children}
        </Authenticator.Provider>
    </Authenticator>
    }
    </div>
  );
}

export default AuthProvider;
