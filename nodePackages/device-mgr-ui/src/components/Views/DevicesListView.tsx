import React, { useEffect, useMemo, useRef, useState } from "react";
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable, { tableInit } from '../Table/Table';
import {
  useFetchDevicesQuery,
  useListTagsQuery,
  useCreateTagMutation,
  Device,
  DeviceTag,
} from '../../services/deviceService';
import { ITEM_LIST_DISPLAY_CNT } from '../../constants';
import DeviceHistory, { DeviceHistoryParameters } from './DeviceHistory';
import { WEB_SOCK_SERVER_ADDR } from '../../constants';

const initialTableState = {
  headers: ['Device id', 'Name', 'Mode', 'Type', 'Path', 'Parent node'],
  rows: [],
  detailBtn: false,
  deleteBtn: false,
  editBtn: false,
} as tableInit;

const DevicesListView: React.FC = () => {
  const [page, setPage] = useState<number>(0);
  const [show, setShow] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [deviceDetail, setDeviceDetail] = useState<Device | null>(null);
  const [filterNodeName, setFilterNodeName] = useState<string>('');
  const [filterName, setFilterName] = useState<string>('');
  const [newTag, setNewTag] = useState<string>('');
  const [tagStatus, setTagStatus] = useState<string>('');
  const [tagError, setTagError] = useState<string>('');

  const ws = useRef<WebSocket | null>(null);

  const {
    data: devicesData,
    isLoading: devicesLoading,
    isError: devicesError,
    refetch: refetchDevices,
  } = useFetchDevicesQuery({
    pageCount: page * ITEM_LIST_DISPLAY_CNT,
    pageSize: ITEM_LIST_DISPLAY_CNT,
    nodeName: filterNodeName,
    deviceName: filterName,
  });

  const [createTag, { isLoading: creatingTag }] = useCreateTagMutation();

  const {
    data: tagsData,
    isLoading: tagsLoading,
    isError: tagsError,
    refetch: refetchTags,
  } = useListTagsQuery(
    { deviceId: deviceDetail?.idDevices ?? 0 },
    {
      skip: !deviceDetail?.idDevices,
    }
  );

  useEffect(() => {
    const wsEndpoint = WEB_SOCK_SERVER_ADDR || 'ws://localhost:8112';

    const accessToken = sessionStorage.getItem('accessToken');
    if (!accessToken) {
      console.warn('Access token not found in sessionStorage');
      return;
    }

    const socket = new WebSocket(`${WEB_SOCK_SERVER_ADDR}?access_token=${encodeURIComponent(accessToken)}`);

    socket.onopen = () => console.log('ws opened');
    socket.onclose = () => console.log('ws closed');
    ws.current = socket;

    return () => {
      socket.close();
      ws.current = null;
    };
  }, []);

  useEffect(() => {
    if (deviceDetail) {
      setNewTag('');
      setTagStatus('');
      setTagError('');
    }
  }, [deviceDetail?.idDevices]);

  const devicesDisplay = useMemo<tableInit>(() => {
    return {
      headers: ['Device id', 'Name', 'Mode', 'Type', 'Path', 'Parent node'],
      rows: devicesData
        ? devicesData.map((device: Device) => [
            device.idDevices.toString(),
            device.name,
            device.mode,
            device.type,
            device.channelPath,
            device.nodeName,
          ])
        : [],
      detailBtn: true,
      deleteBtn: false,
      editBtn: false,
      detailCallback: (devDetails) => {
        const id = parseInt(devDetails[0], 10);
        const selected = devicesData?.find((item: Device) => item.idDevices === id) ?? null;
        if (selected) {
          setDeviceDetail(selected);
          setShow(true);
        }
      },
    } as tableInit;
  }, [devicesData]);

  const handleClose = () => setShow(false);
  const handleCloseHistory = () => setShowHistory(false);
  const handleOpenDeviceHistory = () => setShowHistory(true);

  const handleFilterNodeNameChange = (event: React.ChangeEvent<HTMLInputElement>) => setFilterNodeName(event.target.value);
  const handleFilterNameChange = (event: React.ChangeEvent<HTMLInputElement>) => setFilterName(event.target.value);
  const handleNewTagChange = (event: React.ChangeEvent<HTMLInputElement>) => setNewTag(event.target.value);

  const handleDeviceRefresh = () => {
    refetchDevices();
    if (deviceDetail?.idDevices) {
      refetchTags?.();
    }
  };

  const handleCreateTag = async () => {
    if (!deviceDetail) {
      setTagError('No device selected.');
      return;
    }

    const tag = newTag.trim();
    if (!tag) {
      setTagError('Tag cannot be empty.');
      return;
    }

    try {
      await createTag({ deviceId: deviceDetail.idDevices, tag }).unwrap();
      setNewTag('');
      setTagStatus('Tag added successfully.');
      setTagError('');
      refetchTags?.();
    } catch (error) {
      console.error('Tag creation failed', error);
      setTagStatus('');
      setTagError('Failed to add tag. Please try again.');
    }
  };

  const deviceHistoryArgs = {
    ws: ws.current,
    idDevice: deviceDetail?.idDevices.toString(),
  } as DeviceHistoryParameters;

  return (
    <>
      <Modal show={showHistory} onHide={handleCloseHistory}>
        <Modal.Header closeButton>
          <Modal.Title>Device History</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {ws.current && deviceDetail?.idDevices ? <DeviceHistory {...deviceHistoryArgs} /> : null}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseHistory}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>

      <Modal show={show} onHide={handleClose}>
        <Modal.Header closeButton>
          <Modal.Title>Device details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3" controlId="deviceDetails.id">
              <Form.Label>Device id</Form.Label>
              <Form.Control type="text" placeholder="Device id ..." readOnly defaultValue={deviceDetail?.idDevices} />
            </Form.Group>
            <Form.Group className="mb-3" controlId="deviceDetails.name">
              <Form.Label>Device name</Form.Label>
              <Form.Control type="text" placeholder="name ..." readOnly defaultValue={deviceDetail?.name} />
            </Form.Group>
            <Form.Group className="mb-3" controlId="deviceDetails.mode">
              <Form.Label>Mode</Form.Label>
              <Form.Control type="text" placeholder="mode..." readOnly defaultValue={deviceDetail?.mode} />
            </Form.Group>
            <Form.Group className="mb-3" controlId="deviceDetails.type">
              <Form.Label>Type</Form.Label>
              <Form.Control type="text" placeholder="type ..." readOnly defaultValue={deviceDetail?.type} />
            </Form.Group>
            <Form.Group className="mb-3" controlId="deviceDetails.path">
              <Form.Label>Device path</Form.Label>
              <Form.Control type="text" placeholder="/devicePath/..." readOnly defaultValue={deviceDetail?.channelPath} />
            </Form.Group>
            <Form.Group className="mb-3" controlId="deviceParentNode.name">
              <Form.Label>Parent node</Form.Label>
              <Form.Control type="text" placeholder="parent node..." readOnly defaultValue={deviceDetail?.nodeName} />
            </Form.Group>

            <Form.Group className="mb-3" controlId="deviceDetails.tags">
              <Form.Label>Personal tags</Form.Label>
              {tagsError ? <div className="text-danger mb-2">Unable to load tags.</div> : null}
              {tagsLoading ? (
                <div>Loading tags...</div>
              ) : tagsData && tagsData.length ? (
                <ul className="mb-2">
                  {tagsData.map((tag: DeviceTag) => (
                    <li key={tag.id}>{tag.tag}</li>
                  ))}
                </ul>
              ) : (
                <div className="mb-2">No personal tags added yet.</div>
              )}
              <Form.Control
                type="text"
                placeholder="Add a personal tag"
                value={newTag}
                onChange={handleNewTagChange}
              />
              {tagError ? <div className="text-danger mt-1">{tagError}</div> : null}
              {tagStatus ? <div className="text-success mt-1">{tagStatus}</div> : null}
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>
            Close
          </Button>
          <Button variant="primary" onClick={handleCreateTag} disabled={!newTag.trim() || creatingTag || !deviceDetail}>
            {creatingTag ? 'Adding tag...' : 'Add Tag'}
          </Button>
          <Button variant="primary" onClick={handleOpenDeviceHistory} disabled={!deviceDetail?.idDevices}>
            history
          </Button>
        </Modal.Footer>
      </Modal>

      <Container>
        <Row className="p-3 mb-2 bg-success bg-gradient text-white rounded-3">
          <Col xs={5}>
            <Form>
              <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                <Row xs={12}>
                  <Col xs={2} className="d-flex align-items-center">
                    <Form.Label className="mb-0">Filter</Form.Label>
                  </Col>
                  <Col xs={5}>
                    <Form.Control type="text" placeholder="node name..." value={filterNodeName} onChange={handleFilterNodeNameChange} />
                  </Col>
                  <Col xs={5}>
                    <Form.Control type="text" placeholder="parent node..." value={filterName} onChange={handleFilterNameChange} />
                  </Col>
                </Row>
              </Form.Group>
            </Form>
          </Col>
          <Col>
            <Form className="mr-left ">
              <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                <Row xs={12}>
                  <Col xs={6}>
                    <Button onClick={() => page > 0 && setPage(page - 1)} disabled={page === 0}>
                      Previous page
                    </Button>
                  </Col>
                  <Col xs={1} className="d-flex align-items-center justify-content-center">
                    <Form.Label className="mb-0">{page}</Form.Label>
                  </Col>
                  <Col xs={5}>
                    <Button onClick={() => setPage(page + 1)}>Next page</Button>
                  </Col>
                </Row>
              </Form.Group>
            </Form>
          </Col>
        </Row>

        <Row className="mb-3">
          <Col>
            {devicesError ? <div className="text-danger">Unable to load devices.</div> : null}
            {devicesLoading ? <div>Loading devices...</div> : null}
          </Col>
        </Row>

        <Row>
          <Col>
            <BaseTable {...devicesDisplay} />
          </Col>
        </Row>
      </Container>
    </>
  );
};

export default DevicesListView;
