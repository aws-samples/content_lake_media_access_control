
// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState } from 'react';
import { Flashbar, } from '@cloudscape-design/components';
import { v4 as uuid4 } from 'uuid';


export function useNotifications() {
  const [notices, setNotices] = useState([]);

  const notify = (level, msg, replace_guid) => {
    const guid = replace_guid ? replace_guid : uuid4();
    if (replace_guid) {
      // NOP
    } else {
      setNotices([...notices, {id: guid, level: level, msg: msg}]);
    }
    return guid;
  };

  const notified = (id) => {
    setNotices(notices.filter(item => item.id !== id))
  };

  return {
    notices: notices,
    notifyFn: notify,
    notifiedFn: notified,
  }
}


function Notifications({ notices, notifiedFn }) {
  const items = notices.map(item=>{
    return {
        type: item.level,
        content: item.msg,
        statusIconAriaLabel: item.level,
        dismissLabel: 'Dismiss message',
        dismissible: true,
        onDismiss: () => notifiedFn(item.id),
        id: item.id
    }
  });

  return <Flashbar 
          items={items} />;
};

export default Notifications;
