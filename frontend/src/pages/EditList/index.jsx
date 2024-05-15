// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useRef, useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useCollection } from '@cloudscape-design/collection-hooks';
import { CARD_DEFINITIONS } from './card-config';
import { Pagination, Cards, Checkbox, TextFilter } from '@cloudscape-design/components';
import { Breadcrumbs, FullPageHeader, ToolsContent } from './common-components';
import {
  CustomAppLayout,
  TableEmptyState,
  TableNoMatchState,
} from '../common/common-components';
import Notifications from '../../components/Notifications';
import FileUploadPopup from '../../components/FileUpload/FileUploadPopup';
import ConfirmModal from '../../components/ConfirmModal';
import { paginationLabels } from '../../common/labels';
import { getFilterCounterText } from '../../common/tableCounterStrings';
import axiosInstance from '../../common/AxiosComm';
import { v4 as uuid4 } from 'uuid';
import '../../styles/base.scss';
import { useNavigate } from 'react-router-dom';


function CardContent({ locker, loadHelpPanelContent, notifyFn }) {

  const [showAll, setShowAll] = React.useState(false);
  const [loading, setLoading] = useState(true);
  const [edits, setEdits] = useState([]); 
  const [refreshKey, setRefreshKey] = useState(0);
  const [displayFileUpload, setDisplayFileUpload] = useState(false);
  const [displayConfirmActive, setDisplayConfirmActive] = useState(false);
  const [activeLoading, setActiveLoading] = useState(false);

  const { items, actions, filteredItemsCount, collectionProps, filterProps, paginationProps } = useCollection(
    edits,
    {
      filtering: {
        empty: <TableEmptyState resourceName="Edit" />,
        noMatch: <TableNoMatchState onClearFilter={() => actions.setFiltering('')} />,
      },
      pagination: { pageSize: 20 },
      sorting: { defaultState: { sortingColumn: CARD_DEFINITIONS.sections[0] } },
      selection: {},
    }
  );

  const url = "/lockers/" + locker + "/edits";

  const navigate = useNavigate();

  useEffect(() => { 
    setLoading(true);
    axiosInstance.get(url + (showAll ? "?all=1" : ""))
      .then(response => {
        if (response && response.data) {
          console.log(response.data);
          setEdits(response.data['edit'].map(x => {return {...x, id: x.name, locker: locker}}));
        }
        setLoading(false);
      })
      .catch(error => {
        console.log(error);
        notifyFn("error", "Error getting the locker edit list.");
      });
  }, [refreshKey, locker, showAll]);

  const onCreateCallback = () => {
    setDisplayFileUpload(true);
  };

  const onSaveFileUpload = (results) => {
    const parts = results.upload.split('/');
    const edit_id = parts[parts.length-2];
    notifyFn("success", `Successfully uploaded ${parts[parts.length-1]} as id ${edit_id}`);
    setDisplayFileUpload(false);
    navigate("/lockers/" + locker + "/edits/" + edit_id);
    setRefreshKey(oldKey => oldKey + 1);
  };

  const onCancelFileUpload = () => {
    setDisplayFileUpload(false);
  };

  const onFileUploadError = msg => {
    notifyFn("error", msg);
    setDisplayFileUpload(false);
  };

  const onConfirmActive = () => {
    const selectedItem = collectionProps.selectedItems[0];
    const action = selectedItem.active ? "disable" : "enable";

    setDisplayConfirmActive(false);
    setActiveLoading(true);

    axiosInstance.put("/lockers/" + locker + "/edits/" + selectedItem.id + "/" + action)
    .then(response => {
      console.log(response.data);
      setRefreshKey(oldKey => oldKey + 1);
      setActiveLoading(false);
    })
    .catch(error => {
      console.log(error);
      notifyFn('error', `Unable to ${action} ${selectedItem.id} edit in locker ${locker}.`);
      setActiveLoading(false);
    });
  };

  const selectedActiveMessage = (collectionProps.selectedItems.length ? (collectionProps.selectedItems[0].active ? "Deactivate" : "Activate") : "");

  return (
    <div>
    <FileUploadPopup
      visible={displayFileUpload}
      url={url}
      onCancel={onCancelFileUpload}
      onSave={onSaveFileUpload}
      onError={onFileUploadError}
    />
    <ConfirmModal
      visible={displayConfirmActive}
      header={selectedActiveMessage}
      message={`Are you sure you wish to ${selectedActiveMessage}?`}
      onConfirm={onConfirmActive}
      onDiscard={() => setDisplayConfirmActive(false)}
    />
    <Cards
      {...collectionProps}
      cardDefinition={CARD_DEFINITIONS}
      visibleSections={['id', 'original', 'create_time', 'active']}
      cardsPerRow={[
        { cards: 1 },
        { minWidth: 500, cards: 2 }
      ]}
      loading={loading}
      loadingText="Loading Locker Edits"
      items={items}
      selectionType="single"
      variant="full-page"
      header={
        <FullPageHeader
          selectedItems={collectionProps.selectedItems}
          totalItems={edits}
          locker={locker}
          loadHelpPanelContent={loadHelpPanelContent}
          onCreateCallback={onCreateCallback}
          onActivationClick={() => setDisplayConfirmActive(true)}
          activationLoading={activeLoading}
        />
      }
      filter={
        <div>
        <TextFilter
          {...filterProps}
          filteringAriaLabel="Filter edits"
          filteringPlaceholder="Find edits"
          countText={getFilterCounterText(filteredItemsCount)}
        />
        <br/>
          <Checkbox
           onChange={({ detail }) => setShowAll(detail.checked) }
           checked={showAll}>
            All Edits
          </Checkbox>
        </div>
      }
      pagination={<Pagination {...paginationProps} ariaLabels={paginationLabels} />}
    />
    </div>
  );
}

function EditList() {
  const {locker} = useParams();

  const [toolsOpen, setToolsOpen] = useState(false);
  const appLayout = useRef();

  // notifications
  const [notices, setNotices] = useState([]);
  const notify = (level, msg) => {
    setNotices([...notices, {id: uuid4(), level:level, msg:msg}]);
  };
  const notified = (id) => {
    setNotices(notices.filter(item => item.id !== id))
  };

  return (
    <CustomAppLayout
      ref={appLayout}
      navigationHide={true}
      notifications={<Notifications notices={notices} notifiedFn={notified}/>}
      breadcrumbs={<Breadcrumbs locker={locker}/>}
      content={
        <CardContent
          locker={locker}
          loadHelpPanelContent={() => {
            setToolsOpen(true);
            appLayout.current?.focusToolsClose();
          }}
          notifyFn={notify}
        />
      }
      contentType="table"
      tools={<ToolsContent />}
      toolsOpen={toolsOpen}
      onToolsChange={({ detail }) => setToolsOpen(detail.open)}
      stickyNotifications
    />
  );
}

export default EditList;

