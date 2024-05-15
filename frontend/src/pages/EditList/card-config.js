// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { NavLink } from 'react-router-dom';

export const CARD_DEFINITIONS = {
  sections: [
    {
      id: 'id',
      header: 'Edit ID',
      content: item => (
        <div>
          <NavLink to={`/lockers/${item.locker}/edits/${item.id}`}>{item.id}</NavLink>
        </div>
      ),
    },
    {
      id: 'original',
      header: 'File Name',
      content: item => item.original,
    },
    {
      id: 'create_time',
      content: item => (item.create_time ? item.create_time.substr(0, 10) : ''),
      header: 'Created',
    },
    {
      id: 'active',
      content: item => item.active ? "True" : "False",
      header: 'Active',
    }
  ]
}
