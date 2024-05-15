// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import {
  Box,
  Button,
  Modal,
  SpaceBetween,
} from '@cloudscape-design/components';


function ConfirmModal({ header, message, visible, onDiscard, onConfirm }) {
  return (
    <Modal
      visible={visible}
      onDismiss={onDiscard}
      header={header}
      closeAriaLabel="Close dialog"
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button variant="link" onClick={onDiscard}>Cancel</Button>
            <Button variant="primary" onClick={onConfirm}>Ok</Button>
          </SpaceBetween>
        </Box>
      }
    >
      {message}
    </Modal>
  );
}

export default ConfirmModal;
