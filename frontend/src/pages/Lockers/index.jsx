// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState, useEffect, useRef } from 'react';
import { useCollection } from '@cloudscape-design/collection-hooks';
import { CARD_DEFINITIONS } from './cards-config';
import { Cards, Pagination, Checkbox } from '@cloudscape-design/components';
import { Breadcrumbs, ToolsContent, FullPageHeader } from './common-components';
import {
  CustomAppLayout,
  TableEmptyState,
  TableNoMatchState,
} from '../common/common-components';
import AddLockerModal from './AddLockerModal';
import ConfirmModal from '../../components/ConfirmModal';
import Notifications from '../../components/Notifications';
import { paginationLabels } from '../../common/labels';
import axiosInstance from '../../common/AxiosComm';
import { v4 as uuid4 } from 'uuid';
import '../../styles/base.scss';


const PageSize = 20;


function DetailsCards({ loadHelpPanelContent, notifyFn }) {

  const [showAll, setShowAll] = React.useState(false);
  const [displayAddLocker, setDisplayAddLocker] = useState(false);
  const [displayConfirmActive, setDisplayConfirmActive] = useState(false);
  const [activeLoading, setActiveLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [lockers, setLockers] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);

  const { items, actions, filteredItemsCount, collectionProps, filterProps, paginationProps } = useCollection(
    lockers,
    {
      filtering: {
        empty: <TableEmptyState resourceName="Shot Locker" />,
        noMatch: <TableNoMatchState onClearFilter={() => actions.setFiltering('')} />,
      },
      pagination: { pageSize: PageSize },
      selection: {},
    }
  );

  useEffect(() => {
    setLoading(true);
    axiosInstance.get("/lockers" + (showAll ? "?all=1" : ""))
      .then(response => {
        if (response && response.data) {
          setLockers(response.data['locker'].map(x => {return {...x, 'id': x.name}}));
        }
        setLoading(false);
      })
      .catch(error => {
        console.log(error);
        notifyFn("error", "Error getting the locker list.");
      });
  }, [refreshKey, showAll]);

  const onAdded = (locker) => {
    setDisplayAddLocker(false);
    let arr_lockers = lockers || [];
    setLockers([...arr_lockers, {'id':locker, 'active':true}]);
  };

  const onConfirmActive = () => {
    const selectedItem = collectionProps.selectedItems[0];
    const action = selectedItem.active ? "disable" : "enable";

    setDisplayConfirmActive(false);
    setActiveLoading(true);

    axiosInstance.put("/lockers/" + selectedItem.id + "/" + action)
    .then(response => {
      console.log(response.data);
      setRefreshKey(oldKey => oldKey + 1);
      setActiveLoading(false);
    })
    .catch(error => {
      console.log(error);
      notifyFn('error', `Unable to ${action} ${selectedItem.id} locker.`);
      setActiveLoading(false);
    });
  };

  const selectedActiveMessage = (collectionProps.selectedItems.length ? (collectionProps.selectedItems[0].active ? "Deactivate" : "Activate") : "");

  return (
    <div>
      <AddLockerModal
        visible={displayAddLocker}
        onAdded={onAdded}
        onDiscard={() => setDisplayAddLocker(false)}
        notifyFn={notifyFn}/>
      <ConfirmModal
        visible={displayConfirmActive && !!selectedActiveMessage}
        header={selectedActiveMessage}
        message={`Are you sure you wish to ${selectedActiveMessage}?`}
        onConfirm={onConfirmActive}
        onDiscard={() => setDisplayConfirmActive(false)}
        />
      <Cards
        {...collectionProps}
        stickyHeader={true}
        cardDefinition={CARD_DEFINITIONS}
        visibleSections={['id', 'active']}
        loading={loading}
        loadingText="Loading Content Lake Shot Lockers"
        items={items}
        selectionType="single"
        variant="full-page"
        header={
          <FullPageHeader
            selectedItems={collectionProps.selectedItems}
            totalItems={lockers}
            loadHelpPanelContent={loadHelpPanelContent}
            onAddLockerClick={() => setDisplayAddLocker(true)}
            onActivationClick={() => setDisplayConfirmActive(true)}
            activationLoading={activeLoading}
          />
        }
        filter={
          <Checkbox
           onChange={({ detail }) => setShowAll(detail.checked) }
           checked={showAll}>
            All Lockers
          </Checkbox>
        }
        pagination={<Pagination {...paginationProps} ariaLabels={paginationLabels} disabled={loading} />}
      />
    </div>
  );
}

const Lockers = () => {
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
      breadcrumbs={<Breadcrumbs />}
      content={
        <DetailsCards
          notifyFn={notify}
          loadHelpPanelContent={() => {
            setToolsOpen(true);
            appLayout.current?.focusToolsClose();
          }}
        />
      }
      contentType="cards"
      tools={<ToolsContent />}
      toolsOpen={toolsOpen}
      onToolsChange={({ detail }) => setToolsOpen(detail.open)}
      stickyNotifications={true}
    />
  );
}

export default Lockers;
