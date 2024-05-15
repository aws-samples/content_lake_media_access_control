// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from "react";
import {
  Button,
  Box,
  SpaceBetween,
  Modal,
  FileUpload,
  Spinner,
} from '@cloudscape-design/components';
import axiosInstance from "../../common/AxiosComm";


const FileUploadPopup = props => {
  const [value, setValue] = React.useState([]);
  const [uploading, setUploading] = React.useState(false);
  const [message, setMessage] = React.useState("");

  React.useEffect(() => {   
    setValue([]);
    setUploading(false);
    setMessage("");
  }, [props.visible]);

  const cancelHandler = event => {
    event.preventDefault();
    props.onCancel();
  };

  const onChange = ({ detail }) => {
    if (detail.value && detail.value.length) {
        if (!detail.value[0].name.endsWith(".xml") && 
            !detail.value[0].name.endsWith(".aaf") && 
            !detail.value[0].name.endsWith(".otio")) {
          setMessage("Please select ONLY an AAF, FCP XML, or OpenTimeline IO edit file.");
          return;
        }
    }
    setMessage("");
    setValue(detail.value);
  };

  const onSave = mediaObj => {
    props.onSave(mediaObj);
  };

  const onError = () => {
    props.onError("Unable to Upload File.");
  };

  const fileUpload = (file) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    axiosInstance.post(props.url, formData, {
      headers: {
        "Content-Type": "multipart/form-data"
      },
    })
    .then(response => {
      setUploading(false);
      onSave(response.data);
    })
    .catch(error => {
      setUploading(false);
      onError(error);
    });
  }

  const onFormSubmit = e => {
    e.preventDefault();
    console.log("File to Upload: ");
    console.log(value);
    fileUpload(value[0]);
  };
  
  return (
    <Modal
      onDismiss={cancelHandler}
      visible={props.visible}
      closeAriaLabel="Close modal"
      header="File Upload"
    > 
      <Box variant="span">
        Select an AAF, FCP XML or OpenTimeline IO edit file.
      </Box>


      <SpaceBetween direction="vertical" size="s">
        <FileUpload
          onChange={onChange}
          value={value}
          multiple={false}
          i18nStrings={{
            uploadButtonText: e => "Choose Edit File",
            dropzoneText: e => "Drop file to upload",
            removeFileAriaLabel: e => "Remove file",
            limitShowFewer: "Show fewer files",
            limitShowMore: "Show more files",
            errorIconAriaLabel: "Error"
          }}
          showFileLastModified
          showFileSize
          constraintText={message}
        /> 
        {(value && value.length > 0) &&
        <form onSubmit={onFormSubmit}>
          <SpaceBetween direction="horizontal" size="xs">
            <Button 
              type="submit" 
              onClick={onFormSubmit}
              disabled={!value || !value.length || uploading}
              iconName="upload">
              {uploading && <Spinner/>}
              Upload Edit File
            </Button>
          </SpaceBetween>
        </form>}
      </SpaceBetween>
    </Modal>
  );
};

export default FileUploadPopup;
