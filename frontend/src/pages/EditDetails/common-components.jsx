// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BreadcrumbGroup,
  Button,
  Header,
  SpaceBetween,
} from '@cloudscape-design/components';
import { Auth } from 'aws-amplify';


export const Breadcrumbs = ({locker, editId}) => {
  const items = [
    {
      text: 'ShotLocker',
      href: '/lockers',
    },
    {
      text: locker,
      href: '/lockers/' + locker,
    },
    {
      text: editId,
      href: '#',
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
}

export const PageHeader = ({ locker, editId, buttons }) => {

  const onLogoutClick = event => {
    event.preventDefault();
    Auth.signOut();
  };

  return (
    <Header
      variant="h1"
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button 
            data-testid="header-btn-logout" 
            onClick={onLogoutClick}>
            Logout
          </Button>
        </SpaceBetween>
      }
    >
      {editId}
    </Header>
  );
};

