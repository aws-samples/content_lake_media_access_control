// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Grid,
  Modal,
  FormField,
  SpaceBetween,
  Spinner,
  Select,
} from '@cloudscape-design/components';
import axiosInstance from '../../common/AxiosComm';


function AddLockerModal({ visible, onAdded, onDiscard, notifyFn }) {
  const [selectedBucket, setSelectedBucket] = React.useState(null);
  const [loading, setLoading] = useState('pending');
  const [adding, setAdding] = useState(false);
  const [available, setAvailable] = useState([]);

  useEffect(() => {   
    setSelectedBucket(null);
  }, [visible]);

  const fetchData = () => {   
    setLoading('loading');
    setAvailable([]);
    axiosInstance.get("/lockers?available=1")
      .then(response => {
        if (response && response.data) {
          setAvailable(response.data['locker'].map(x => {return {'label': x.name, 'value': x.name}}));
        }
        setLoading('finished');
      })
      .catch(error => {
        setLoading('error');
        console.log(error);
        notifyFn('error', `Unable to get the available bucket list.`);
      });
  };

  const handleLoadItems = ({ detail: { filteringText, firstPage, samePage } }) => {
    fetchData();
  };

  const onRefreshClick = (event) => {
    event.preventDefault();
    fetchData();
  };

  const onSelected = (option) => {
    console.log(option);
    setSelectedBucket(option);
  };

  const onLockerAdd = event => {
    event.preventDefault();
    setAdding(true);
    const locker = selectedBucket.value;
    axiosInstance.put("/lockers/" + locker + "/enable")
    .then(response => {
      setAdding(false);
      console.log(response.data);
      onAdded(locker);
    })
    .catch(error => {
      console.log(error);
      notifyFn('error', `Unable to enable Amazon S3 bucket.`);
      setAdding(false);
      onDiscard();
    });
  };

  return (
    <Modal
      visible={visible}
      onDismiss={onDiscard}
      header='Create Shot Locker'
      closeAriaLabel="Close dialog"
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button variant="link" onClick={onDiscard}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={onLockerAdd} 
              disabled={!selectedBucket || loading !== 'finished' || adding}>
              {adding && <Spinner/>}
              Mark as Shot Locker
            </Button>
          </SpaceBetween>
        </Box>
      }
    >
      <SpaceBetween size="m">

        <Box variant="span">
          Select Content Lake S3 Bucket in the account to use as a Shot Locker. 
        </Box>

        <FormField label={'Available Content Lake Amazon S3 Buckets'} stretch={true}>
          <Grid gridDefinition={[{ colspan: 10 }, { colspan: 2 }]}>
            <Select
              selectedOption={selectedBucket}
              onChange={ event => onSelected(event.detail.selectedOption) }
              options={available}
              statusType={loading}
              placeholder="Choose a Content Lake Amazon S3 bucket"
              empty="No Amazon S3 buckets available"
              loadingText="loading..."
              finishedText="[end of results]"
              errorText="Error loading available buckets"
              onLoadItems={handleLoadItems}
            />
            <Button 
              disabled={loading !== "finished"} 
              onClick={onRefreshClick} 
              iconName="refresh"
            />
        </Grid>
        </FormField>

      </SpaceBetween>
    </Modal>
  );
}

export default AddLockerModal;
