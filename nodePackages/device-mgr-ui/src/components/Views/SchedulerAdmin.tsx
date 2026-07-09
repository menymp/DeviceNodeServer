// src/components/Views/SchedulerAdmin.tsx
import React, { useEffect, useRef, useState } from 'react';
import {
  Container,
  Row,
  Col,
  Button,
  Table,
  Modal,
  Form,
  Alert,
  Spinner,
} from 'react-bootstrap';
import { useSelector } from 'react-redux';
import type { RootState } from '../../store';
import {
  useFetchRulesQuery,
  useFetchRuleByIdQuery,
  useCreateRuleMutation,
  useUpdateRuleMutation,
  useDeleteRuleMutation,
  useNotifyReloadMutation,
  SchedulerRule,
  SchedulerRulePayload,
} from '../../services/schedulerService';
import { useNavigate } from 'react-router-dom';

const PAGE_SIZE = 50;

const prettyJson = (obj: any) => {
  try {
    return JSON.stringify(obj, null, 2);
  } catch {
    return String(obj ?? '');
  }
};

const parseJsonSafe = (s: string) => {
  try {
    return JSON.parse(s);
  } catch {
    return null;
  }
};

const SchedulerAdmin: React.FC = () => {
  const navigate = useNavigate();
  const auth = useSelector((s: RootState) => s.auth);
  const isAdmin = !!(auth?.is_admin);

  // list rules
  const [page] = useState<number>(0);
  const { data: rules = [], isFetching: rulesLoading, refetch: refetchRules } = useFetchRulesQuery({ page, size: PAGE_SIZE });

  // selected rule details (lazy fetch by id)
  const [selectedRuleId, setSelectedRuleId] = useState<number | null>(null);
  const { data: selectedRule, isFetching: selectedRuleLoading, refetch: refetchSelectedRule } =
    useFetchRuleByIdQuery(
      { id: selectedRuleId ?? -1 },
      { skip: selectedRuleId === null }
    );

  // create / edit modal
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingRule, setEditingRule] = useState<SchedulerRule | null>(null);
  const [formName, setFormName] = useState<string>('');
  const [formEnabled, setFormEnabled] = useState<boolean>(true);
  const [formRuleJsonText, setFormRuleJsonText] = useState<string>('');
  const [formSafeStateText, setFormSafeStateText] = useState<string>('');
  const [formError, setFormError] = useState<string | null>(null);

  // delete modal
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<SchedulerRule | null>(null);

  // messages
  const [message, setMessage] = useState<{ type: 'info' | 'success' | 'danger'; text: string } | null>(null);

  // RTK mutations
  const [createRule, { isLoading: creating }] = useCreateRuleMutation();
  const [updateRule, { isLoading: updating }] = useUpdateRuleMutation();
  const [deleteRule, { isLoading: deleting }] = useDeleteRuleMutation();
  const [notifyReload, { isLoading: notifying }] = useNotifyReloadMutation();

  // focus first input when modal opens
  const nameInputRef = useRef<HTMLInputElement | null>(null);
  useEffect(() => {
    if (showEditModal) {
      setTimeout(() => nameInputRef.current?.focus(), 100);
    }
  }, [showEditModal]);

  // helper to show messages
  const showMsg = (type: 'info' | 'success' | 'danger', text: string) => {
    setMessage({ type, text });
    window.setTimeout(() => setMessage(null), 6000);
  };

  // open create modal
  const openCreate = () => {
    setEditingRule(null);
    setFormName('');
    setFormEnabled(true);
    setFormRuleJsonText(JSON.stringify({ start_time: '08:00:00', weekdays: ['mon','tue','wed','thu','fri'], topic: 'devices/1/set', on_payload: 'ON', off_payload: 'OFF' }, null, 2));
    setFormSafeStateText(JSON.stringify({ topic: 'devices/1/set', payload: 'OFF' }, null, 2));
    setFormError(null);
    setShowEditModal(true);
  };

  // open edit modal
  const openEdit = (rule: SchedulerRule) => {
    setEditingRule(rule);
    setFormName(rule.name);
    setFormEnabled(Boolean(rule.enabled));
    setFormRuleJsonText(prettyJson(rule.rule_json ?? {}));
    setFormSafeStateText(prettyJson(rule.safe_state ?? {}));
    setFormError(null);
    setShowEditModal(true);
  };

  // validate and build payload
  const buildPayloadFromForm = (): { payload?: SchedulerRulePayload; error?: string } => {
    if (!formName.trim()) return { error: 'Name is required' };
    const parsedRule = parseJsonSafe(formRuleJsonText);
    if (parsedRule === null) return { error: 'Invalid JSON for rule_json' };
    let parsedSafe: any = null;
    if (formSafeStateText.trim()) {
      parsedSafe = parseJsonSafe(formSafeStateText);
      if (parsedSafe === null) return { error: 'Invalid JSON for safe_state' };
    }
    const payload: SchedulerRulePayload = {
      name: formName.trim(),
      enabled: formEnabled,
      rule_json: parsedRule,
      safe_state: parsedSafe,
    };
    return { payload };
  };

  // submit create or update
  const handleSubmit = async () => {
    setFormError(null);
    const { payload, error } = buildPayloadFromForm();
    if (error) {
      setFormError(error);
      return;
    }
    try {
      if (editingRule) {
        await updateRule({ id: editingRule.id, payload: payload! }).unwrap();
        showMsg('success', `Updated rule "${payload!.name}"`);
      } else {
        const res = await createRule(payload!).unwrap();
        showMsg('success', `Created rule "${payload!.name}" (id ${res.id})`);
      }
      setShowEditModal(false);
      // refresh list and selected
      refetchRules();
      if (editingRule) {
        setSelectedRuleId(editingRule.id);
        refetchSelectedRule();
      }
    } catch (err: any) {
      console.error(err);
      setFormError(err?.data?.message || err?.message || 'Failed to save rule');
    }
  };

  // confirm delete
  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteRule({ id: deleteTarget.id }).unwrap();
      showMsg('success', `Deleted rule "${deleteTarget.name}"`);
      setShowDeleteModal(false);
      setDeleteTarget(null);
      refetchRules();
      if (selectedRuleId === deleteTarget.id) {
        setSelectedRuleId(null);
      }
    } catch (err: any) {
      console.error(err);
      showMsg('danger', err?.data?.message || err?.message || 'Failed to delete rule');
    }
  };

  // notify scheduler to reload rules (server endpoint)
  const handleNotifyReload = async () => {
    try {
      await notifyReload().unwrap();
      showMsg('success', 'Scheduler reload requested');
    } catch (err: any) {
      console.error(err);
      showMsg('danger', 'Failed to request scheduler reload');
    }
  };

  // view details
  const handleView = (rule: SchedulerRule) => {
    setSelectedRuleId(rule.id);
  };

  // guard
  if (!isAdmin) {
    return (
      <Container className="py-4">
        <Row>
          <Col>
            <Alert variant="danger">Unauthorized. Admin access required to manage scheduler rules.</Alert>
          </Col>
        </Row>
      </Container>
    );
  }

  return (
    <Container className="py-4">
      <Row className="mb-3">
        <Col>
          <h3>Scheduler Admin</h3>
          <p className="text-muted">Create, view, edit and remove scheduled commands. Use Notify Reload after changes to prompt the scheduler to pick up updates immediately.</p>
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

      <Row className="mb-3">
        <Col md={8}>
          <Button variant="primary" onClick={openCreate} className="me-2">Create Rule</Button>
          <Button variant="outline-secondary" onClick={() => refetchRules()} className="me-2">
            {rulesLoading ? <Spinner animation="border" size="sm" /> : 'Refresh List'}
          </Button>
          <Button variant="outline-info" onClick={handleNotifyReload} disabled={notifying}>
            {notifying ? <Spinner animation="border" size="sm" /> : 'Notify Scheduler Reload'}
          </Button>
        </Col>
      </Row>

      <Row>
        <Col md={8}>
          <h5>Rules</h5>
          {rulesLoading ? (
            <Spinner />
          ) : rules.length ? (
            <Table striped bordered hover size="sm">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Enabled</th>
                  <th>Updated At</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((r) => (
                  <tr key={r.id}>
                    <td>{r.id}</td>
                    <td>{r.name}</td>
                    <td>{r.enabled ? 'Yes' : 'No'}</td>
                    <td>{r.updated_at ? new Date(r.updated_at).toLocaleString() : '-'}</td>
                    <td>
                      <Button size="sm" variant="outline-primary" onClick={() => handleView(r)} className="me-1">View</Button>
                      <Button size="sm" variant="outline-secondary" onClick={() => openEdit(r)} className="me-1">Edit</Button>
                      <Button size="sm" variant="outline-danger" onClick={() => { setDeleteTarget(r); setShowDeleteModal(true); }}>Delete</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          ) : (
            <div className="text-muted">No rules found.</div>
          )}
        </Col>

        <Col md={4}>
          <h5>Selected Rule</h5>
          {selectedRuleId === null ? (
            <div className="text-muted">No rule selected. Click View to see details.</div>
          ) : selectedRuleLoading ? (
            <Spinner />
          ) : selectedRule ? (
            <div>
              <h6>{selectedRule.name} (id {selectedRule.id})</h6>
              <p><strong>Enabled:</strong> {selectedRule.enabled ? 'Yes' : 'No'}</p>
              <p><strong>Created:</strong> {selectedRule.created_at ?? '-'}</p>
              <p><strong>Updated:</strong> {selectedRule.updated_at ?? '-'}</p>
              <div>
                <strong>Rule JSON</strong>
                <pre style={{ maxHeight: 220, overflow: 'auto', background: '#f8f9fa', padding: 8 }}>{prettyJson(selectedRule.rule_json)}</pre>
              </div>
              <div className="mt-2">
                <strong>Safe State</strong>
                <pre style={{ maxHeight: 160, overflow: 'auto', background: '#f8f9fa', padding: 8 }}>{prettyJson(selectedRule.safe_state)}</pre>
              </div>
            </div>
          ) : (
            <div className="text-muted">Rule not found.</div>
          )}
        </Col>
      </Row>

      {/* Create / Edit Modal */}
      <Modal show={showEditModal} onHide={() => setShowEditModal(false)} size="lg" centered>
        <Modal.Header closeButton>
          <Modal.Title>{editingRule ? `Edit Rule: ${editingRule.name}` : 'Create Rule'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {formError && <Alert variant="danger">{formError}</Alert>}
          <Form>
            <Form.Group className="mb-2">
              <Form.Label>Name</Form.Label>
              <Form.Control
                ref={nameInputRef}
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="Rule name"
              />
            </Form.Group>

            <Form.Group className="mb-2">
              <Form.Check
                type="checkbox"
                label="Enabled"
                checked={formEnabled}
                onChange={(e) => setFormEnabled(e.target.checked)}
              />
            </Form.Group>

            <Form.Group className="mb-2">
              <Form.Label>Rule JSON</Form.Label>
              <Form.Control
                as="textarea"
                rows={8}
                value={formRuleJsonText}
                onChange={(e) => setFormRuleJsonText(e.target.value)}
                placeholder='{"start_time":"08:00:00","weekdays":["mon","tue"],"topic":"devices/1/set","on_payload":"ON","off_payload":"OFF"}'
              />
              <Form.Text className="text-muted">Provide the rule JSON. Example fields: start_time, end_time, weekdays, months, duration_minutes, topic, on_payload, off_payload.</Form.Text>
            </Form.Group>

            <Form.Group className="mb-2">
              <Form.Label>Safe State (optional)</Form.Label>
              <Form.Control
                as="textarea"
                rows={4}
                value={formSafeStateText}
                onChange={(e) => setFormSafeStateText(e.target.value)}
                placeholder='{"topic":"devices/1/set","payload":"OFF"}'
              />
              <Form.Text className="text-muted">Optional JSON to apply when rule is disabled or on service start.</Form.Text>
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowEditModal(false)}>Cancel</Button>
          <Button variant="primary" onClick={handleSubmit} disabled={creating || updating}>
            {(creating || updating) ? <Spinner animation="border" size="sm" /> : (editingRule ? 'Save Changes' : 'Create Rule')}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Delete confirmation */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Delete Rule</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete rule <strong>{deleteTarget?.name}</strong> (id {deleteTarget?.id})?
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>Cancel</Button>
          <Button variant="danger" onClick={confirmDelete} disabled={deleting}>
            {deleting ? <Spinner animation="border" size="sm" /> : 'Delete'}
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default SchedulerAdmin;
