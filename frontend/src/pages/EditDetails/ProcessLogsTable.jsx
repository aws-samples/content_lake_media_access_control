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
import axiosInstance from '../../common/AxiosComm';


const LOGS_COLUMN_DEFINITIONS = [
  {
    id: 'name',
    header: 'User or Role',
    cell: item => item.user_role_arn,
  },
  {
    id: 'expired_date',
    header: 'Expiry Date',
    cell: item => item.expired_date,
  },
];

export function ProcessLogTable({locker, editId, notifyFn}) {

  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {   
    setLoading(true);
    setSelectedItems([]);
    axiosInstance.get("/lockers/" + locker + "/edits/" + editId + "/logs")
      .then(response => {
        if (response && response.data) {
          console.log(response.data);
          setLogs(response.data['logs']);
        }
        setLoading(false);
      })
      .catch(error => {
        console.log(error);
        notifyFn('error', `Unable to get the ${locker} locker edit process logs.`);
      });
  }, [refreshKey]);

  return (
    <div>
    <Table
      className="process-logs-table"
      columnDefinitions={LOGS_COLUMN_DEFINITIONS}
      loading={loading}
      loadingText="Loading Process Logs"
      items={logs}
      selectionType="none"
      header={
        <TableHeader
          title="Process Logs"
          selectedItems={selectedItems}
          totalItems={access}
          actionButtons={
            <SpaceBetween direction="horizontal" size="xs">
              <Button 
                onClick={() => console.log("click")}>
                Refresh
              </Button>
            </SpaceBetween>
          }
        />
      }
      empty={
        <Box textAlign="center" color="inherit">
          <b>No logs</b>
          <Box
            padding={{ bottom: "s" }}
            variant="p"
            color="inherit"
          >
            No logs to display.
          </Box>
        </Box>
      }
    />
    </div>
  );
}

export default ProcessLogsTable;
