// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  SpaceBetween,
  Table,
} from '@cloudscape-design/components';
import { TableHeader } from '../common/common-components';
import AddUserModal from './AddUserModal';
import DeleteModal from '../../components/DeleteModal';
import axiosInstance from '../../common/AxiosComm';


const ACCESS_COLUMN_DEFINITIONS = [
  {
    id: 'name',
    header: 'IAM User or Role',
    cell: item => item.user_role_arn,
  },
  {
    id: 'expired_date',
    header: 'Expiry Date',
    cell: item => item.expired_date,
  },
];

export function AccessTable({locker, editId, notifyFn}) {

  const [displayAddUser, setDisplayAddUser] = useState(false);
  const [displayDeleteUser, setDisplayDeleteUser] = useState(false);
  const [access, setAccess] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedItems, setSelectedItems] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);

  const atLeastOneSelected = selectedItems.length > 0;

  useEffect(() => {   
    setLoading(true);
    setSelectedItems([]);
    axiosInstance.get("/lockers/" + locker + "/edits/" + editId + "/access")
      .then(response => {
        if (response && response.data) {
          console.log(response.data);
          setAccess(response.data['access']);
        }
        setLoading(false);
      })
      .catch(error => {
        console.log(error);
        notifyFn('error', `Unable to get the ${locker} locker edit access list.`);
      });
  }, [refreshKey, locker, editId, notifyFn]);

  const onUserAdd = (user_role_arn, expiryDate) => {
    return new Promise((resolve, reject) => {
      axiosInstance.put("/lockers/" + locker + "/edits/" + editId + "/access/grant/" + expiryDate + "/" + user_role_arn)
      .then(response => {
        console.log(response.data);
        setDisplayAddUser(false);
        setRefreshKey(oldKey => oldKey + 1);
        resolve(response);
      })
      .catch(error => {
        console.log(error);
        notifyFn('error', `Unable to add user to ${locker} locker edit access list.`);
        reject(error);
      });

    });
  };

  const onUserDelete = () => {
    const user_role_arn = selectedItems[0].user_role_arn;
    axiosInstance.put("/lockers/" + locker + "/edits/" + editId + "/access/deny/" + user_role_arn)
    .then(response => {
      console.log(response.data);
      setRefreshKey(oldKey => oldKey + 1);
      setDisplayDeleteUser(false);
    })
    .catch(error => {
      console.log(error);
      notifyFn('error', `Unable to revoke user access.`);
      setDisplayDeleteUser(false);
    });
  };

  return (
    <div>
      <DeleteModal
        name="Selected IAM User/Role"
        visible={displayDeleteUser}
        items={selectedItems}
        onDiscard={() => setDisplayDeleteUser(false)}
        onDelete={onUserDelete}/>
      <AddUserModal
       visible={displayAddUser}
       onAdd={onUserAdd}
       onDiscard={() => setDisplayAddUser(false)}/>
    <Table
      className="access-table"
      columnDefinitions={ACCESS_COLUMN_DEFINITIONS}
      loading={loading}
      loadingText="Loading IAM User/Role Access"
      items={access}
      selectionType="single"
      selectedItems={selectedItems}
      onSelectionChange={event => setSelectedItems(event.detail.selectedItems)}
      header={
        <TableHeader
          title="Access"
          selectedItems={selectedItems}
          totalItems={access}
          actionButtons={
            <SpaceBetween direction="horizontal" size="xs">
              <Button 
                disabled={!atLeastOneSelected}
                onClick={() => setDisplayDeleteUser(true)}>
                Delete
              </Button>
              <Button
                onClick={() => setDisplayAddUser(true)}>
                Add IAM User or Role
              </Button>
            </SpaceBetween>
          }
        />
      }
      empty={
        <Box textAlign="center" color="inherit">
          <b>No resources</b>
          <Box
            padding={{ bottom: "s" }}
            variant="p"
            color="inherit"
          >
            No resources to display.
          </Box>
        </Box>
      }
    />
    </div>
  );
}

export default AccessTable;
