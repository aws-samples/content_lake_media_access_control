// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import {
  Alert,
  Box,
  Button,
  Link,
  Modal,
  SpaceBetween,
  Spinner,
} from '@cloudscape-design/components';



function DeleteModal({ name, items, visible, onDiscard, onDelete }) {
  const [deleting, setDeleting] = React.useState(false);
  const isMultiple = items.length > 1;

  const onDeleteCallback = event => {
    event.preventDefault();
    setDeleting(true);
    onDelete()
      .then(results => setDeleting(false))
      .catch(err => setDeleting(false));
  };

  return (
    <Modal
      visible={visible}
      onDismiss={onDiscard}
      header={isMultiple ? `Delete ${name}s` : `Delete ${name}`}
      closeAriaLabel="Close dialog"
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button variant="link" onClick={onDiscard}>
              Cancel
            </Button>
            <Button variant="primary" onClick={onDeleteCallback} disabled={deleting}>
              {deleting && <Spinner/>}
              Delete
            </Button>
          </SpaceBetween>
        </Box>
      }
    >
      {items.length > 0 && (
        <SpaceBetween size="m">
          {isMultiple ? (
            <Box variant="span">
              Delete{' '}
              <Box variant="span" fontWeight="bold">
                {items.length} {name + 's'}
              </Box>{' '}
              permanently? This action cannot be undone.
            </Box>
          ) : (
            <Box variant="span">
              Delete {name + ' '}
              <Box variant="span" fontWeight="bold">
                {name[0].id}
              </Box>{' '}
              permanently? This action cannot be undone.
            </Box>
          )}

          <Alert statusIconAriaLabel="Info">
            Proceeding with this action will delete {name}(s) with all content and can impact related resources.{' '}
            <Link external={true} href="#">
              Learn more
            </Link>
          </Alert>
        </SpaceBetween>
      )}
    </Modal>
  );
}

export default DeleteModal;
