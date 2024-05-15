// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { NavLink } from 'react-router-dom';

export const CARD_DEFINITIONS = {
  sections: [
    {
      id: 'id',
      header: 'Shot Locker',
      content: item => {
        return item.active ? 
          <NavLink to={"/lockers/" + item.id} fontSize="heading-m">
            {item.id}
          </NavLink>
        : item.id;
      }
    },
    {
      id: 'active',
      content: item => item.active ? "True" : "False",
      header: 'Active',
    }
  ]
};

