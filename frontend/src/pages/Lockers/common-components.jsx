// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { BreadcrumbGroup, Button, HelpPanel, SpaceBetween, Spinner } from '@cloudscape-design/components';
import { TableHeader } from '../common/common-components';
import { Auth } from 'aws-amplify';


export const Breadcrumbs = () => (
  <BreadcrumbGroup 
    items={[{text: 'ShotLocker', href: '/lockers'}]} 
    expandAriaLabel="Show path" 
    ariaLabel="Breadcrumbs" />
);

export const FullPageHeader = ({
  resourceName = 'Lockers',
  extraActions = null,
  ...props
}) => {

  const isOnlyOneSelected = props.selectedItems.length === 1;
  const isSelectedActive = isOnlyOneSelected && props.selectedItems[0].active;

  const onActivationClick = event => {
    event.preventDefault();
    props.onActivationClick(props.selectedItems[0]);
  };

  const onAddLockerClick = event => {
    event.preventDefault();
    props.onAddLockerClick();
  };

  const onLogoutClick = event => {
    event.preventDefault();
    Auth.signOut();
  };

  return (
    <TableHeader
      variant="awsui-h1-sticky"
      title={resourceName}
      actionButtons={
        <SpaceBetween size="xs" direction="horizontal">
          {extraActions}
          <Button 
            data-testid="header-btn-view-details" 
            disabled={!isOnlyOneSelected}
            onClick={onActivationClick}>
            {props.activationLoading && <Spinner/>}
            {isSelectedActive ? "Deactivate" : "Activate"}
          </Button>
          <Button 
            data-testid="header-btn-create"
            variant="primary"
            onClick={onAddLockerClick}>
            Create Shot Locker
          </Button>
          <Button 
           data-testid="header-btn-logout" 
           onClick={onLogoutClick}>
            Logout
          </Button>
        </SpaceBetween>
      }
      {...props}
    />
  );
};

export const ToolsContent = () => (
  <HelpPanel header={<h2>Lockers</h2>}>
    <p>
      View your current Shot Lockers.  To drill down even further into the details, 
      choose the name of an individual Shot Locker. To Mark a Content Lake S3 Bucket to
      be used as Shot Locker, click Create Shot Locker.
    </p>
  </HelpPanel>
);


