// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Modal,
  Input,
  FormField,
  SpaceBetween,
  DatePicker,
  Spinner,
} from '@cloudscape-design/components';


function AddUserModal({ visible, onDiscard, onAdd }) {
  const [userInputText, setUserInputText] = useState('');
  const [expiryDate, setExpiryDate] = React.useState("");
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    setUserInputText('');
    setExpiryDate('');
  }, [visible]);

  const onUserAdd = event => {
    event.preventDefault();
    setAdding(true);
    onAdd(userInputText, expiryDate)
      .then(results => setAdding(false))
      .catch(err => setAdding(false));
  };

  return (
    <Modal
      visible={visible}
      onDismiss={onDiscard}
      header='Add IAM User or Role'
      closeAriaLabel="Close dialog"
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button variant="link" onClick={onDiscard}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={onUserAdd} 
              disabled={!userInputText || ! expiryDate || adding}>
              {adding && <Spinner/>}
              Add
            </Button>
          </SpaceBetween>
        </Box>
      }
    >
        <SpaceBetween size="m">

          <Box variant="span">
            Grant Access to an IAM User or Role.
          </Box>

          <FormField label={'User or Role ARN'}>
            <Input
              onChange={event => setUserInputText(event.detail.value)}
              value={userInputText}
              ariaRequired={true}
            />
          </FormField>

          <FormField
            label="Access expiry"
            constraintText="Use YYYY/MM/DD format."
          >
            <DatePicker
              onChange={({ detail }) => setExpiryDate(detail.value.replace('/', '-'))}
              value={expiryDate}
              openCalendarAriaLabel={selectedDate =>
                "Choose Access expiry date" +
                (selectedDate
                  ? `, selected date is ${selectedDate}`
                  : "")
              }
              nextMonthAriaLabel="Next month"
              placeholder="YYYY/MM/DD"
              previousMonthAriaLabel="Previous month"
              todayAriaLabel="Today"
            />
          </FormField>

        </SpaceBetween>
    </Modal>
  );
}

export default AddUserModal;
