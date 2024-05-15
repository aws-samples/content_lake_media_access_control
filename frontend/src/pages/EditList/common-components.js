// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { BreadcrumbGroup, Button, HelpPanel, SpaceBetween, Spinner } from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';
import { TableHeader } from '../common/common-components';
import { Auth } from 'aws-amplify';

export const Breadcrumbs = ({locker}) => {
  const items = [
    {
      text: 'ShotLocker',
      href: '/lockers',
    },
    {
      text: locker,
      href: '/lockers/' + locker,
    },
  ];

  const navigate = useNavigate();

  const onBreadcrumbClick = event => {
    event.preventDefault();
    console.log('Breadcrumb nav to ' + event.detail.href)
    navigate(event.detail.href);
  };

  return (
    <BreadcrumbGroup 
      items={items} 
      expandAriaLabel="Show path" 
      onClick={onBreadcrumbClick}
      ariaLabel="Breadcrumbs" />
  );
};


export const FullPageHeader = ({
  resourceName = 'Edits',
  extraActions = null,
  ...props
}) => {

  const isOnlyOneSelected = props.selectedItems.length === 1;
  const isSelectedActive = isOnlyOneSelected && props.selectedItems[0].active;

  const onActivationClick = event => {
    event.preventDefault();
    console.log(props.selectedItems);
    props.onActivationClick(props.selectedItems[0]);
  };

  const onCreateClick = event => {
    event.preventDefault();
    props.onCreateCallback();
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
            onClick={onCreateClick}>
            Upload Edit
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
  <HelpPanel
    header={<h2>Edit Details</h2>}
  >
    <p>
      View the uploaded edits to this Shot Locker and related information such as the
      uploaded edit filename and timestamp. To drill down even further into the details, 
      choose the name of an individual edit and press the View Details button.
    </p>
  </HelpPanel>
);



