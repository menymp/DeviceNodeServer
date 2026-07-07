// src/pages/Login.tsx
import React, { useEffect, useState } from 'react';
import { Container, Row, Col, Card, Form, Button } from 'react-bootstrap';
import { useLoginMutation } from '../../services/authService';
import { useAppDispatch, useAppSelector } from '../../storeHooks';
import { setCredentials } from '../../store';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [login, { isLoading }] = useLoginMutation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const auth = useAppSelector((s) => s.auth);

  useEffect(() => {
    // if already logged in, redirect
    if (auth.accessToken) {
      navigate('/');
    }
  }, [auth.accessToken, navigate]);

  const decodeJwt = (token: string) => {
    try {
      const payload = token.split('.')[1];
      const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
      return JSON.parse(decodeURIComponent(
        decoded
          .split('')
          .map((c) => `%${('00' + c.charCodeAt(0).toString(16)).slice(-2)}`)
          .join('')
      ));
    } catch {
      return {} as Record<string, unknown>;
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      alert('Please enter username and password');
      return;
    }

    try {
      const res = await login({ username, password }).unwrap();
      if (res && res.access_token) {
        const tokenPayload = decodeJwt(res.access_token);
        const userIdFromToken = tokenPayload.sub ? Number(tokenPayload.sub) : null;
        const userId = res.user_id ?? res.idUser ?? res.userId ?? userIdFromToken;
        const isAdmin = tokenPayload.is_admin ?? false;

        dispatch(setCredentials({ accessToken: res.access_token, userId, is_admin: isAdmin }));

        if (typeof window !== 'undefined' && window.sessionStorage) {
          window.sessionStorage.setItem('accessToken', res.access_token);
          window.sessionStorage.setItem('user', username);
          if (userId !== null && !Number.isNaN(userId)) {
            window.sessionStorage.setItem('userId', String(userId));
          } else {
            window.sessionStorage.removeItem('userId');
          }
        }

        navigate('/');
      } else {
        alert('Login failed: invalid response from server');
      }
    } catch (err: any) {
      const msg = err?.data?.error || err?.error || 'Login failed';
      alert(`Login failed: ${msg}`);
    }
  };

  return (
    <Container>
      <Row className="vh-100 d-flex justify-content-center align-items-center">
        <Col md={8} lg={6} xs={12}>
          <div className="border border-3 border-primary"></div>
          <Card className="shadow">
            <Card.Body>
              <div className="mb-3 mt-md-4">
                <h2 className="fw-bold mb-2 text-uppercase ">Device Node System</h2>
                <p className="mb-5">Please enter your login and password!</p>
                <Form onSubmit={handleLogin}>
                  <Form.Group className="mb-3" controlId="formUsername">
                    <Form.Label>Username</Form.Label>
                    <Form.Control
                      type="text"
                      placeholder="Enter username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                    />
                  </Form.Group>

                  <Form.Group className="mb-3" controlId="formPassword">
                    <Form.Label>Password</Form.Label>
                    <Form.Control
                      type="password"
                      placeholder="Password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                  </Form.Group>

                  <div className="d-grid">
                    <Button variant="primary" type="submit" disabled={isLoading}>
                      {isLoading ? 'Logging in...' : 'Login'}
                    </Button>
                  </div>
                </Form>

                <div className="mt-3">
                  <p className="mb-0 text-center">
                    Don't have an account?{' '}
                    <a href="/register" className="text-primary fw-bold">
                      Sign Up
                    </a>
                  </p>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}
