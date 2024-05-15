// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useEffect } from 'react';
import {
  Box,
  ColumnLayout,
  Container,
  Header,
  Spinner,
  Button,
  SpaceBetween,
} from '@cloudscape-design/components';
import ProcessStatusIndicator from '../../components/ProcessStatusIndicator';
import axiosInstance from '../../common/AxiosComm';
import CopyText from '../../common/copy-text';


const EditSummary = ({locker, editId, notifyFn}) => {
  const [name, setName] = useState('');
  const [manifest, setManifest] = useState('');
  const [created, setCreated] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {   
    setLoading(true);
    axiosInstance.get("/lockers/" + locker + "/edits/" + editId)
      .then(response => {
        if (response && response.data) {
          console.log(response.data);
          setManifest(response.data['manifest']);
          const parts = response.data['original'].split('/');
          setName(parts[parts.length-1]);
          setCreated(response.data['create_time'].substr(0,10))
          setStatus(response.data['process_status'])
        }
        setLoading(false);
      })
      .catch(error => {
        console.log(error);
        notifyFn("error", "Error getting the locker edit information.");
        setLoading(false);
      });
  }, [refreshKey, locker, editId, notifyFn]);

  const onRefreshClick = event => {
    event.preventDefault();
    setRefreshKey(oldKey => oldKey + 1);
  };

  const header = (<Header 
                    variant="h2"
                    actions={
                      <SpaceBetween direction="horizontal" size="xs">
                        <Button disabled={loading} onClick={onRefreshClick} iconName="refresh"/>
                      </SpaceBetween>
                    }>
                    Edit Summary
                    </Header>);

  return (
    <Container header={header}>
      <ColumnLayout columns={4} variant="text-grid">
        <div>
          <Box variant="awsui-key-label">Name</Box>
          <div>
            {loading ? <Spinner/> : name}
          </div>
        </div>
        <div>
          <Box variant="awsui-key-label">Created</Box>
          <div>
            {loading ? <Spinner/> : created}
          </div>
        </div>
        <div>
          <Box variant="awsui-key-label">Process Status</Box>
          <div>
            {loading ? <Spinner/> : <ProcessStatusIndicator status={status}/>}
          </div>
        </div>
        <div>
          <Box variant="awsui-key-label">Manifest</Box>
          {(manifest && !loading) &&
          <CopyText
            copyText={manifest}
            copyButtonLabel="Copy S3 URI"
            successText="S3 URI copied"
            errorText="S3 URI failed to copy"
          />
          }
          {(!manifest && !loading) && "-"}
          {loading && <Spinner/>}
        </div>
      </ColumnLayout>
    </Container>
  );
}

export default EditSummary;
