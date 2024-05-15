// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { StatusIndicator, } from '@cloudscape-design/components';


function ProcessStatusIndicator({status}) {
  if (status === "SUCCEEDED") {
    return <StatusIndicator>Success</StatusIndicator>;
  }
  else if (status === "RUNNING") {
    return (<StatusIndicator type="in-progress"> In progress </StatusIndicator>);
  }
  else if (status === "FAILED") {
    return (<StatusIndicator type="error"> Failed </StatusIndicator>);
  }
  else if (status === "TIMED_OUT") {
    return (<StatusIndicator type="warning"> Timed Out </StatusIndicator>);
  }
  else if (status === "ABORTED") {
    return (<StatusIndicator type="warning"> Aborted </StatusIndicator>);
  }
  else {
    return (<StatusIndicator type="warning"> Unknown </StatusIndicator>);
  }
}

export default ProcessStatusIndicator;