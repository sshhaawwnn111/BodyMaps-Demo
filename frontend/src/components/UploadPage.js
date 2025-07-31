import React, { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Card, Button, Alert, ProgressBar, Form, Modal } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const UploadPage = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [currentCaseName, setCurrentCaseName] = useState('');
  const [status, setStatus] = useState({});
  const [uploadedCases, setUploadedCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState('');
  const [sliceIndex, setSliceIndex] = useState(50);
  const [showLogs, setShowLogs] = useState(false);
  const [logs, setLogs] = useState([]);
  const [alert, setAlert] = useState({ show: false, message: '', variant: 'info' });
  const [dragOver, setDragOver] = useState(false);
  
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadUploadedCases();
  }, []);

  useEffect(() => {
    let interval;
    if (processing && currentCaseName) {
      interval = setInterval(() => {
        checkStatus(currentCaseName);
      }, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [processing, currentCaseName]);

  const loadUploadedCases = async () => {
    try {
      const response = await axios.get('/api/list_uploads');
      setUploadedCases(response.data.uploads || []);
    } catch (error) {
      console.error('Error loading cases:', error);
    }
  };

  const showAlert = (message, variant = 'info') => {
    setAlert({ show: true, message, variant });
    setTimeout(() => setAlert({ show: false, message: '', variant: 'info' }), 5000);
  };

  const handleFileSelect = (selectedFile) => {
    if (selectedFile && selectedFile.name.toLowerCase().endsWith('.nii.gz')) {
      setFile(selectedFile);
      showAlert(`Selected file: ${selectedFile.name}`, 'success');
    } else {
      showAlert('Please select a .nii.gz file', 'danger');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    handleFileSelect(droppedFile);
  };

  const handleUpload = async () => {
    if (!file) {
      showAlert('Please select a file first', 'warning');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.success) {
        setCurrentCaseName(response.data.case_name);
        showAlert(response.data.message, 'success');
        loadUploadedCases();
        setFile(null);
      }
    } catch (error) {
      showAlert(error.response?.data?.error || 'Upload failed', 'danger');
    } finally {
      setUploading(false);
    }
  };

  const handleProcessing = async (caseName) => {
    try {
      const response = await axios.post('/api/run_docker', { case_name: caseName });
      if (response.data.success) {
        setProcessing(true);
        setCurrentCaseName(caseName);
        showAlert('Processing started...', 'info');
      }
    } catch (error) {
      showAlert(error.response?.data?.error || 'Failed to start processing', 'danger');
    }
  };

  const checkStatus = async (caseName) => {
    try {
      const response = await axios.get(`/api/status/${caseName}`);
      setStatus(response.data);

      if (response.data.status === 'completed') {
        setProcessing(false);
        showAlert('Processing completed! Redirecting to results...', 'success');
        setTimeout(() => navigate(`/results/${caseName}`), 2000);
      } else if (response.data.status === 'error') {
        setProcessing(false);
        showAlert(`Processing failed: ${response.data.message}`, 'danger');
      }
    } catch (error) {
      console.error('Error checking status:', error);
    }
  };

  const handleDeleteCase = async (caseName) => {
    if (window.confirm(`Are you sure you want to delete ${caseName}?`)) {
      try {
        await axios.delete(`/api/delete_upload/${caseName}`);
        showAlert(`${caseName} deleted successfully`, 'success');
        loadUploadedCases();
        if (currentCaseName === caseName) {
          setCurrentCaseName('');
          setProcessing(false);
        }
      } catch (error) {
        showAlert('Failed to delete case', 'danger');
      }
    }
  };

  const handleSliceInteraction = async (event) => {
    if (!selectedCase) return;

    const rect = event.target.getBoundingClientRect();
    const x = Math.floor((event.clientX - rect.left) * (event.target.naturalWidth / rect.width));
    const y = Math.floor((event.clientY - rect.top) * (event.target.naturalHeight / rect.height));

    try {
      await axios.post('/api/interact_segment', {
        case_name: selectedCase,
        x: x,
        y: y,
        z: sliceIndex
      });
      // Refresh the slice image to show segmentation
      const img = event.target;
      img.src = `/api/segmentation_preview/${selectedCase}/${sliceIndex}?t=${Date.now()}`;
    } catch (error) {
      console.error('Segmentation interaction failed:', error);
    }
  };

  const loadLogs = async () => {
    if (!currentCaseName) return;
    try {
      const response = await axios.get(`/api/logs/${currentCaseName}`);
      setLogs(response.data.logs || []);
    } catch (error) {
      console.error('Error loading logs:', error);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'uploaded': return <span className="status-indicator status-uploaded"></span>;
      case 'running': return <span className="status-indicator status-running"></span>;
      case 'completed': return <span className="status-indicator status-completed"></span>;
      case 'error': return <span className="status-indicator status-error"></span>;
      default: return null;
    }
  };

  return (
    <Container className="mt-5">
      {/* Header */}
      <div className="demo-info text-center">
        <h1><i className="fas fa-brain"></i> BodyMaps SuPreM Segmentation Demo</h1>
        <p className="lead mb-0">Upload CT scans (.nii.gz) and get AI-powered organ segmentation results</p>
        <small>Developed for Johns Hopkins CCVL Lab - Project II Application</small>
      </div>

      {/* Alert */}
      {alert.show && (
        <Alert variant={alert.variant} dismissible onClose={() => setAlert({ show: false, message: '', variant: 'info' })}>
          {alert.message}
        </Alert>
      )}

      {/* Features */}
      <Row className="mb-4">
        <Col md={4}>
          <Card className="feature-card h-100">
            <Card.Body className="text-center">
              <i className="fas fa-upload fa-3x text-primary mb-3"></i>
              <h5>Easy Upload</h5>
              <p>Drag & drop .nii.gz CT scan files</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card className="feature-card h-100">
            <Card.Body className="text-center">
              <i className="fas fa-brain fa-3x text-success mb-3"></i>
              <h5>AI Processing</h5>
              <p>SuPreM model segmentation in Docker</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card className="feature-card h-100">
            <Card.Body className="text-center">
              <i className="fas fa-download fa-3x text-info mb-3"></i>
              <h5>Download Results</h5>
              <p>Get segmented organs as ZIP files</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Upload Section */}
      <Row>
        <Col lg={6}>
          <Card>
            <Card.Header>
              <h4><i className="fas fa-cloud-upload-alt"></i> Upload CT Scan</h4>
            </Card.Header>
            <Card.Body>
              <div
                className={`upload-area ${dragOver ? 'dragover' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <i className="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
                <h5>Drop your .nii.gz file here</h5>
                <p className="text-muted">or click to browse</p>
                {file && (
                  <div className="mt-3">
                    <strong>Selected: {file.name}</strong>
                  </div>
                )}
              </div>
              <input
                type="file"
                ref={fileInputRef}
                style={{ display: 'none' }}
                accept=".nii.gz"
                onChange={(e) => handleFileSelect(e.target.files[0])}
              />
              <div className="mt-3">
                <Button
                  variant="primary"
                  onClick={handleUpload}
                  disabled={!file || uploading}
                  className="w-100"
                >
                  {uploading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2"></span>
                      Uploading...
                    </>
                  ) : (
                    <>
                      <i className="fas fa-upload me-2"></i>
                      Upload File
                    </>
                  )}
                </Button>
              </div>
            </Card.Body>
          </Card>
        </Col>

        {/* Case Management */}
        <Col lg={6}>
          <Card>
            <Card.Header>
              <h4><i className="fas fa-list"></i> Uploaded Cases</h4>
            </Card.Header>
            <Card.Body>
              {uploadedCases.length === 0 ? (
                <p className="text-muted">No cases uploaded yet.</p>
              ) : (
                <div>
                  {uploadedCases.map((caseItem) => (
                    <div key={caseItem.case_name} className="d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
                      <div>
                        {getStatusIcon(status.status)}
                        <strong>{caseItem.case_name}</strong>
                        <br />
                        <small className="text-muted">{caseItem.files.join(', ')}</small>
                      </div>
                      <div>
                        <Button
                          size="sm"
                          variant="success"
                          onClick={() => handleProcessing(caseItem.case_name)}
                          disabled={processing}
                          className="me-2"
                        >
                          <i className="fas fa-play"></i>
                        </Button>
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() => handleDeleteCase(caseItem.case_name)}
                        >
                          <i className="fas fa-trash"></i>
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>

          {/* Processing Status */}
          {processing && (
            <Card className="mt-3">
              <Card.Header>
                <h5><i className="fas fa-cogs"></i> Processing Status</h5>
              </Card.Header>
              <Card.Body>
                <div className="mb-3">
                  <strong>Case:</strong> {currentCaseName}
                </div>
                <div className="mb-3">
                  <strong>Status:</strong> {status.message || 'Processing...'}
                </div>
                <ProgressBar animated now={100} variant="info" className="mb-3" />
                <Button
                  variant="outline-secondary"
                  size="sm"
                  onClick={() => {
                    setShowLogs(true);
                    loadLogs();
                  }}
                >
                  <i className="fas fa-terminal"></i> View Logs
                </Button>
              </Card.Body>
            </Card>
          )}
        </Col>
      </Row>

      {/* Interactive Viewer */}
      {selectedCase && (
        <Row className="mt-4">
          <Col>
            <Card>
              <Card.Header>
                <h4><i className="fas fa-eye"></i> Interactive Viewer</h4>
              </Card.Header>
              <Card.Body>
                <Form.Group className="mb-3">
                  <Form.Label>Select Case:</Form.Label>
                  <Form.Select
                    value={selectedCase}
                    onChange={(e) => setSelectedCase(e.target.value)}
                  >
                    <option value="">Choose a case...</option>
                    {uploadedCases.map((caseItem) => (
                      <option key={caseItem.case_name} value={caseItem.case_name}>
                        {caseItem.case_name}
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>

                <div className="slice-controls">
                  <Form.Label>Slice: {sliceIndex}</Form.Label>
                  <Form.Range
                    min="0"
                    max="100"
                    value={sliceIndex}
                    onChange={(e) => setSliceIndex(parseInt(e.target.value))}
                    className="slice-slider"
                  />
                </div>

                <div className="interactive-viewer text-center">
                  <img
                    src={`/api/original_slice/${selectedCase}/${sliceIndex}`}
                    alt={`Slice ${sliceIndex}`}
                    className="img-fluid"
                    onClick={handleSliceInteraction}
                    style={{ maxWidth: '500px', cursor: 'crosshair' }}
                  />
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Logs Modal */}
      <Modal show={showLogs} onHide={() => setShowLogs(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Processing Logs</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="logs-container">
            {logs.length === 0 ? (
              <p>No logs available</p>
            ) : (
              logs.map((log, index) => (
                <div key={index}>{log}</div>
              ))
            )}
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowLogs(false)}>
            Close
          </Button>
          <Button variant="primary" onClick={loadLogs}>
            Refresh
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default UploadPage;