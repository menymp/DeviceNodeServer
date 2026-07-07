// src/pages/AdminRfidManager.tsx
import React, { useEffect, useRef, useState } from 'react';
import {
  Container,
  Row,
  Col,
  Button,
  Form,
  Modal,
  Table,
  Alert,
  Spinner,
} from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import type { RootState } from '../../store';
import {
  useResolveRfidMutation,
  useLazyFetchUserRfidsQuery,
  useCreateUserRfidMutation,
  useDeleteUserRfidMutation,
  useFetchUserRfidsQuery,
  UserRfid,
} from '../../services/rfidService';

type ResolveResult = {
  idUser: number;
  username: string;
};

const AdminRfidManager: React.FC = () => {
  const navigate = useNavigate();

  // --- Auth / admin guard
  const auth = useSelector((s: RootState) => s.auth);
  const isAdmin = !!(auth?.is_admin);

  // --- Local UI state
  const scanInputRef = useRef<HTMLInputElement | null>(null);
  const [scanValue, setScanValue] = useState<string>('');
  const [message, setMessage] = useState<{ type: 'info' | 'success' | 'danger'; text: string } | null>(null);

  // For user lookup by id
  const [lookupUserId, setLookupUserId] = useState<number | ''>('');
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);

  // For assign/reassign modal
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignRfidValue, setAssignRfidValue] = useState<string>('');
  const [assignTargetUserId, setAssignTargetUserId] = useState<number | ''>('');
  const [pendingReassign, setPendingReassign] = useState<{ existingUserId: number; existingUsername?: string } | null>(null);

  // For delete confirmation
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{ userId: number; rfidId: number; rfidValue?: string } | null>(null);

  // --- RTK Query hooks
  const [resolveRfid, { isLoading: resolving }] = useResolveRfidMutation();
  const [triggerFetchUserRfids, { data: lazyUserRfids, isFetching: lazyFetching }] = useLazyFetchUserRfidsQuery();
  const [createUserRfid, { isLoading: creating }] = useCreateUserRfidMutation();
  const [deleteUserRfid, { isLoading: deleting }] = useDeleteUserRfidMutation();

  // Also use the standard query for selectedUserId to keep cache-driven updates
  const { data: selectedUserRfids, isFetching: selectedUserRfidsLoading, refetch: refetchSelectedUserRfids } =
    useFetchUserRfidsQuery(
      selectedUserId ? { userId: selectedUserId } : ({} as any),
      {
        skip: !selectedUserId,
      }
    );

  // Focus the scan input when the page mounts and whenever the user navigates back here
  useEffect(() => {
    scanInputRef.current?.focus();
  }, []);

  // Helper to show messages
  const showMsg = (type: 'info' | 'success' | 'danger', text: string) => {
    setMessage({ type, text });
    window.setTimeout(() => setMessage(null), 6000);
  };

  // --- Handlers

  // When RFID scanner sends data it usually ends with Enter. We handle Enter to process the scanned value.
  const handleScanKeyDown: React.KeyboardEventHandler<HTMLInputElement> = async (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const rfid = scanValue.trim();
      if (!rfid) {
        showMsg('info', 'No RFID scanned.');
        return;
      }
      await handleResolveRfid(rfid);
      setScanValue('');
      // keep focus for next scan
      setTimeout(() => scanInputRef.current?.focus(), 50);
    }
  };

  // Resolve RFID -> find user
  const handleResolveRfid = async (rfid: string) => {
    try {
      const res = await resolveRfid({ rfid_id: rfid }).unwrap();
      // res: { idUser, username }
      showMsg('success', `RFID ${rfid} belongs to user ${res.username} (id ${res.idUser}).`);
      // load that user's rfids into the UI
      setSelectedUserId(res.idUser);
      // refetch via RTK query hook
      refetchSelectedUserRfids();
    } catch (err: any) {
      // If not found, allow quick assign
      showMsg('danger', `RFID ${rfid} not assigned to any user.`);
      // open assign modal prefilled
      setAssignRfidValue(rfid);
      setAssignTargetUserId('');
      setPendingReassign(null);
      setShowAssignModal(true);
    }
  };

  // Lookup rfids for a user id (manual input)
  const handleLookupUserRfids = async () => {
    if (!lookupUserId) {
      showMsg('info', 'Enter a user id to lookup.');
      return;
    }
    setSelectedUserId(Number(lookupUserId));
    // use the cached query refetch
    refetchSelectedUserRfids();
  };

  // Assign RFID to user (create)
  const handleAssignRfid = async () => {
    const userId = Number(assignTargetUserId);
    const rfid = assignRfidValue.trim();
    if (!userId || !rfid) {
      showMsg('info', 'Provide both user id and RFID value.');
      return;
    }

    try {
      // If pendingReassign exists, remove from existing user first
      if (pendingReassign) {
        // find the existing user rfids to delete the specific rfid record
        // We will attempt to fetch the existing user's rfids and delete the matching rfid_id
        try {
          const existingRfids = await triggerFetchUserRfids({ userId: pendingReassign.existingUserId }).unwrap();
          const match = existingRfids.find((r) => r.rfid_id === rfid);
          if (match) {
            await deleteUserRfid({ userId: pendingReassign.existingUserId, rfidId: match.id }).unwrap();
            showMsg('info', `Removed RFID ${rfid} from user ${pendingReassign.existingUserId}.`);
          } else {
            // If no exact match, still continue to create for new user
            showMsg('info', `No exact RFID record found on user ${pendingReassign.existingUserId}, continuing assignment.`);
          }
        } catch (err) {
          // ignore and continue
        }
      }

      const created = await createUserRfid({
        userId,
        payload: { rfid_id: rfid, enabled: true },
      }).unwrap();

      showMsg('success', `Assigned RFID ${rfid} to user ${userId}. (record id ${created.id})`);
      setShowAssignModal(false);
      // refresh selected user rfids if it matches
      if (selectedUserId === userId) refetchSelectedUserRfids();
    } catch (err: any) {
      console.error(err);
      showMsg('danger', `Failed to assign RFID: ${err?.data?.message || err?.message || 'unknown error'}`);
    }
  };

  // Reassign flow: when resolving an rfid that belongs to another user, we set pendingReassign and open modal
  const handlePrepareReassign = (rfid: string, existingUserId: number, existingUsername?: string) => {
    setPendingReassign({ existingUserId, existingUsername });
    setAssignRfidValue(rfid);
    setAssignTargetUserId('');
    setShowAssignModal(true);
  };

  // Remove RFID from a user (delete)
  const handleRemoveRfid = (userId: number, rfidRecord: UserRfid) => {
    setDeleteTarget({ userId, rfidId: rfidRecord.id, rfidValue: rfidRecord.rfid_id });
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteUserRfid({ userId: deleteTarget.userId, rfidId: deleteTarget.rfidId }).unwrap();
      showMsg('success', `Removed RFID ${deleteTarget.rfidValue} from user ${deleteTarget.userId}.`);
      setShowDeleteModal(false);
      // refresh if viewing that user
      if (selectedUserId === deleteTarget.userId) refetchSelectedUserRfids();
    } catch (err: any) {
      console.error(err);
      showMsg('danger', `Failed to remove RFID: ${err?.data?.message || err?.message || 'unknown error'}`);
    }
  };

  // Quick UI helper to handle manual assign modal open
  const openAssignForRfid = (rfid: string) => {
    setAssignRfidValue(rfid);
    setAssignTargetUserId('');
    setPendingReassign(null);
    setShowAssignModal(true);
  };

  // --- Render guard for non-admins
  if (!isAdmin) {
    return (
      <Container className="py-4">
        <Row>
          <Col>
            <Alert variant="danger">Unauthorized. Admin access required to use the RFID admin interface.</Alert>
            <Button onClick={() => navigate(-1)}>Go back</Button>
          </Col>
        </Row>
      </Container>
    );
  }

  return (
    <Container className="py-4">
      <Row className="mb-3">
        <Col>
          <h3>RFID Admin</h3>
          <p className="text-muted">Scan an RFID with your USB reader or use the manual controls below.</p>
        </Col>
      </Row>

      {message && (
        <Row className="mb-2">
          <Col>
            <Alert variant={message.type === 'danger' ? 'danger' : message.type === 'success' ? 'success' : 'info'}>
              {message.text}
            </Alert>
          </Col>
        </Row>
      )}

      <Row className="align-items-center mb-3">
        <Col md={6}>
          <Form.Group controlId="rfidScan">
            <Form.Label><strong>Scan RFID</strong></Form.Label>
            <Form.Control
              ref={scanInputRef}
              value={scanValue}
              onChange={(e) => setScanValue(e.target.value)}
              onKeyDown={handleScanKeyDown}
              placeholder="Place cursor here and scan with USB RFID reader (press Enter after scan)"
              autoComplete="off"
            />
            <Form.Text className="text-muted">Scanner typically sends the tag and an Enter key.</Form.Text>
          </Form.Group>
        </Col>

        <Col md={6} className="d-flex gap-2">
          <Button
            variant="primary"
            onClick={() => {
              // manual resolve of current scanValue
              if (!scanValue.trim()) {
                showMsg('info', 'Type or scan an RFID first.');
                scanInputRef.current?.focus();
                return;
              }
              handleResolveRfid(scanValue.trim());
              setScanValue('');
            }}
            disabled={resolving}
          >
            {resolving ? <Spinner animation="border" size="sm" /> : 'Resolve RFID'}
          </Button>

          <Button
            variant="secondary"
            onClick={() => {
              openAssignForRfid(scanValue.trim());
              setScanValue('');
              setTimeout(() => scanInputRef.current?.focus(), 50);
            }}
          >
            Assign RFID
          </Button>

          <Button
            variant="outline-secondary"
            onClick={() => {
              setScanValue('');
              scanInputRef.current?.focus();
            }}
          >
            Clear
          </Button>
        </Col>
      </Row>

      <Row className="mb-4">
        <Col md={6}>
          <h5>Lookup RFIDs by User</h5>
          <Form className="d-flex gap-2 align-items-center">
            <Form.Control
              type="number"
              placeholder="User ID"
              value={lookupUserId}
              onChange={(e) => setLookupUserId(e.target.value === '' ? '' : Number(e.target.value))}
            />
            <Button onClick={handleLookupUserRfids}>Lookup</Button>
            <Button
              variant="outline-secondary"
              onClick={() => {
                setLookupUserId('');
                setSelectedUserId(null);
              }}
            >
              Clear
            </Button>
          </Form>
          <div className="mt-3">
            {selectedUserId ? (
              <>
                <h6>RFIDs for user {selectedUserId}</h6>
                {selectedUserRfidsLoading ? (
                  <Spinner />
                ) : selectedUserRfids && selectedUserRfids.length ? (
                  <Table striped bordered hover size="sm">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>RFID</th>
                        <th>Label</th>
                        <th>Enabled</th>
                        <th>Created</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedUserRfids.map((r) => (
                        <tr key={r.id}>
                          <td>{r.id}</td>
                          <td>{r.rfid_id}</td>
                          <td>{r.label ?? '-'}</td>
                          <td>{r.enabled ? 'Yes' : 'No'}</td>
                          <td>{new Date(r.created_at).toLocaleString()}</td>
                          <td>
                            <Button
                              size="sm"
                              variant="outline-danger"
                              onClick={() => handleRemoveRfid(selectedUserId, r)}
                            >
                              Remove
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                ) : (
                  <div className="text-muted">No RFIDs found for this user.</div>
                )}
              </>
            ) : (
              <div className="text-muted">No user selected.</div>
            )}
          </div>
        </Col>

        <Col md={6}>
          <h5>Quick Actions</h5>
          <p className="text-muted">Use these to quickly assign or reassign tags.</p>

          <div className="mb-2">
            <Button
              variant="outline-primary"
              onClick={() => {
                // open assign modal with empty values
                setAssignRfidValue('');
                setAssignTargetUserId('');
                setPendingReassign(null);
                setShowAssignModal(true);
              }}
            >
              Assign RFID to User
            </Button>
          </div>

          <div className="mb-2">
            <Form.Label>Resolve RFID (manual)</Form.Label>
            <Form.Control
              placeholder="Enter RFID value"
              onKeyDown={async (e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  const val = (e.target as HTMLInputElement).value.trim();
                  if (val) {
                    await handleResolveRfid(val);
                    (e.target as HTMLInputElement).value = '';
                  }
                }
              }}
            />
          </div>

          <div className="mt-3">
            <small className="text-muted">
              When an RFID is already assigned to another user, you can reassign it here — the existing assignment will be removed.
            </small>
          </div>
        </Col>
      </Row>

      {/* Assign / Reassign Modal */}
      <Modal show={showAssignModal} onHide={() => setShowAssignModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>{pendingReassign ? 'Reassign RFID' : 'Assign RFID'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {pendingReassign && (
            <Alert variant="warning">
              RFID currently assigned to user {pendingReassign.existingUserId}
              {pendingReassign.existingUsername ? ` (${pendingReassign.existingUsername})` : ''}.
              Assigning will remove it from that user.
            </Alert>
          )}

          <Form.Group className="mb-2">
            <Form.Label>RFID value</Form.Label>
            <Form.Control
              value={assignRfidValue}
              onChange={(e) => setAssignRfidValue(e.target.value)}
              placeholder="e.g. 04A3B2C1"
            />
          </Form.Group>

          <Form.Group className="mb-2">
            <Form.Label>Target User ID</Form.Label>
            <Form.Control
              type="number"
              value={assignTargetUserId}
              onChange={(e) => setAssignTargetUserId(e.target.value === '' ? '' : Number(e.target.value))}
              placeholder="User ID to assign to"
            />
          </Form.Group>

          <Form.Group className="mb-2">
            <Form.Label>Enabled</Form.Label>
            <Form.Check type="checkbox" defaultChecked />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAssignModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleAssignRfid} disabled={creating}>
            {creating ? <Spinner animation="border" size="sm" /> : pendingReassign ? 'Reassign' : 'Assign'}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Delete confirmation */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Remove RFID</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to remove RFID <strong>{deleteTarget?.rfidValue}</strong> from user{' '}
          <strong>{deleteTarget?.userId}</strong>?
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDelete} disabled={deleting}>
            {deleting ? <Spinner animation="border" size="sm" /> : 'Remove'}
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default AdminRfidManager;
