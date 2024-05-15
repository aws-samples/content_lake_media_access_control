// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { forwardRef } from 'react';
import {
  AppLayout,
  Box,
  Button,
  Header,
  Link,
  SpaceBetween,
} from '@cloudscape-design/components';

export const TableNoMatchState = props => (
  <Box margin={{ vertical: 'xs' }} textAlign="center" color="inherit">
    <SpaceBetween size="xxs">
      <div>
        <b>No matches</b>
        <Box variant="p" color="inherit">
          We can't find a match.
        </Box>
      </div>
      <Button onClick={props.onClearFilter}>Clear filter</Button>
    </SpaceBetween>
  </Box>
);

export const TableEmptyState = ({ resourceName }) => (
  <Box margin={{ vertical: 'xs' }} textAlign="center" color="inherit">
    <SpaceBetween size="xxs">
      <div>
        <b>No {resourceName.toLowerCase()}s</b>
        <Box variant="p" color="inherit">
          No {resourceName.toLowerCase()}s associated with this resource.
        </Box>
      </div>
    </SpaceBetween>
  </Box>
);

export const TableHeader = props => {
  return (
    <Header
      variant={props.variant}
      description={props.description}
      actions={props.actionButtons}
    >
      {props.title}
    </Header>
  );
};

export const CustomAppLayout = forwardRef((props, ref) => {
  return (
    <AppLayout
      ref={ref}
      {...props}
      headerSelector="#header"
      onNavigationChange={event => {
        if (props.onNavigationChange) {
          props.onNavigationChange(event);
        }
      }}
      onToolsChange={event => {
        if (props.onToolsChange) {
          props.onToolsChange(event);
        }
      }}
    />
  );
});

export const CounterLink = ({ children }) => {
  return (
    <Link variant="awsui-value-large" href="#">
      {children}
    </Link>
  );
};
