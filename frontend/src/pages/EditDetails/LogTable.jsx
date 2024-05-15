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
import { formatIso8601 } from '../../common/format';


const LOGS_COLUMN_DEFINITIONS = [
  {
    id: 'id',
    header: 'ID',
    cell: item => item.Index,
  },
  {
    id: 'create_time',
    header: 'Timestamp',
    cell: item => item.CreateTimeFormatted,
  },
  {
    id: 'message',
    header: 'Message',
    cell: item => item.Message,
  },
];

export function LogTable({locker, editId, notifyFn}) {

  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  var visibleColumns = ['create_time', 'message'];

  const parseLogs = (logs) => {
    if (!logs) {
        logs = [];
    }
    const formatTable = (item, index) => {
      item.Index = index;
      item.CreateTimeFormatted = formatIso8601(item.CreateTime);
      return item;
    };
    setLogs(logs.map(formatTable));
  };

  useEffect(() => {   
    setLoading(true);
    axiosInstance.get("/lockers/" + locker + "/edits/" + editId + "/logs")
      .then(response => {
        if (response && response.data) {
          parseLogs(response.data['log']);
        }
        setLoading(false);
      })
      .catch(error => {
        console.log(error);
        notifyFn('error', `Unable to get the ${editId} edit logs.`);
      });
  }, [refreshKey]);

  const onRefreshClick = event => {
    event.preventDefault();
    setRefreshKey(oldKey => oldKey + 1);
  };

  return (
    <div>
    <Table
      className="log-table"
      columnDefinitions={LOGS_COLUMN_DEFINITIONS}
      loading={loading}
      loadingText="Loading logs..."
      items={logs}
      visibleColumns={visibleColumns}
      header={
        <TableHeader
          title="Log Events"
          actionButtons={
            <SpaceBetween direction="horizontal" size="xs">
              <Button disabled={loading} onClick={onRefreshClick} iconName="refresh"/>
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

export default LogTable;
