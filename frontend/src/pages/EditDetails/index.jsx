// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, {useState} from 'react';
import { useParams } from 'react-router-dom';
import { AppLayout, ContentLayout, SpaceBetween } from '@cloudscape-design/components';
import { Breadcrumbs, PageHeader } from './common-components';
import AccessTable from './AccessTable';
import EditSummary from './EditSummary';
import LogTable from './LogTable';
import Notifications from '../../components/Notifications';
import { v4 as uuid4 } from 'uuid';
import '../../styles/base.scss';


const EditDetails = () => {

  const {locker, editId} = useParams();

  // notifications
  const [notices, setNotices] = useState([]);
  const notify = (level, msg) => {
    setNotices([...notices, {id: uuid4(), level:level, msg:msg}]);
  };
  const notified = (id) => {
    setNotices(notices.filter(item => item.id !== id))
  };

  return (
    <AppLayout
      content={
        <ContentLayout header={ <PageHeader locker={locker} editId={editId}/> } >
          <SpaceBetween size="l">
            <EditSummary locker={locker} editId={editId} notifyFn={notify}/>
            <AccessTable locker={locker} editId={editId} notifyFn={notify}/>
            <LogTable locker={locker} editId={editId} notifyFn={notify}/>
          </SpaceBetween>
        </ContentLayout>
      }
      headerSelector="#header"
      breadcrumbs={<Breadcrumbs locker={locker} editId={editId}/>}
      navigationHide={true}
      toolsHide={true}
      contentType="default"
      notifications={<Notifications notices={notices} notifiedFn={notified}/>}
    />
  );
}

export default EditDetails;


