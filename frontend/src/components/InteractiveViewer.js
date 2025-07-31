import React, { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Card, Button, Form, Alert, Badge } from 'react-bootstrap';
import axios from 'axios';

const InteractiveViewer = () => {
  const [uploadedCases, setUploadedCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState('');
  const [imageInfo, setImageInfo] = useState(null);
  const [currentSlice, setCurrentSlice] = useState(0);
  const [maxSlice, setMaxSlice] = useState(100);
  const [interactionMode, setInteractionMode] = useState('positive'); // 'positive' or 'negative'
  const [interactionPoints, setInteractionPoints] = useState([]);
  const [segmentationStats, setSegmentationStats] = useState(null);
  const [alert, setAlert] = useState({ show: false, message: '', variant: 'info' });
  const [loading, setLoading] = useState(false);
  
  const originalImageRef = useRef(null);

  useEffect(() => {
    loadUploadedCases();
  }, []);

  useEffect(() => {
    if (selectedCase) {
      loadImageInfo();
      setCurrentSlice(Math.floor(maxSlice / 2)); // Start at middle slice
    }
  }, [selectedCase]);

  useEffect(() => {
    if (selectedCase && imageInfo) {
      loadSliceImages();
      loadInteractionPoints();
    }
  }, [selectedCase, currentSlice, imageInfo]);

  const loadUploadedCases = async () => {
    try {
      const response = await axios.get('/api/list_uploads');
      setUploadedCases(response.data.uploads || []);
    } catch (error) {
      console.error('Error loading cases:', error);
      showAlert('Error loading cases', 'danger');
    }
  };

  const loadImageInfo = async () => {
    if (!selectedCase) return;
    
    try {
      console.log('Loading image info for case:', selectedCase);
      const response = await axios.get(`/api/image_info/${selectedCase}`);
      console.log('Image info response:', response.data);
      
      if (response.data.success) {
        setImageInfo(response.data.info);
        setMaxSlice(response.data.info.max_slice);
        setCurrentSlice(Math.floor(response.data.info.max_slice / 2));
        showAlert(`Loaded case ${selectedCase} with ${response.data.info.max_slice + 1} slices`, 'success');
      } else {
        showAlert(`Failed to load image info: ${response.data.error}`, 'danger');
      }
    } catch (error) {
      console.error('Error loading image info:', error);
      showAlert(`Error loading image information: ${error.message}`, 'danger');
    }
  };

  const loadSliceImages = async () => {
    if (!selectedCase) return;
    
    // Load original slice with overlay, fallback to original slice
    if (originalImageRef.current) {
      const overlayUrl = `/api/slice_with_overlay/${selectedCase}/${currentSlice}?t=${Date.now()}`;
      const fallbackUrl = `/api/original_slice/${selectedCase}/${currentSlice}?t=${Date.now()}`;
      
      console.log('Loading original image with overlay:', overlayUrl);
      originalImageRef.current.src = overlayUrl;
      
      originalImageRef.current.onerror = (e) => {
        console.error('Failed to load overlay image, trying fallback:', overlayUrl, e);
        // Try fallback to original slice
        originalImageRef.current.src = fallbackUrl;
        originalImageRef.current.onerror = (e2) => {
          console.error('Failed to load fallback image:', fallbackUrl, e2);
          showAlert(`Failed to load CT slice image. Please check if the case exists.`, 'danger');
        };
        originalImageRef.current.onload = () => {
          console.log('Fallback image loaded successfully');
        };
      };
      
      originalImageRef.current.onload = () => {
        console.log('Overlay image loaded successfully');
      };
    }
    
  };

  const loadInteractionPoints = async () => {
    if (!selectedCase) return;
    
    try {
      const response = await axios.get(`/api/get_interaction_points/${selectedCase}/${currentSlice}`);
      if (response.data.success) {
        setInteractionPoints(response.data.points);
      }
    } catch (error) {
      console.error('Error loading interaction points:', error);
    }
  };

  const showAlert = (message, variant = 'info') => {
    setAlert({ show: true, message, variant });
    setTimeout(() => setAlert({ show: false, message: '', variant: 'info' }), 5000);
  };

  const handleImageClick = async (event) => {
    if (!selectedCase) {
      showAlert('Please select a case first', 'warning');
      return;
    }

    if (!imageInfo) {
      showAlert('Image information not loaded yet', 'warning');
      return;
    }

    setLoading(true);
    const rect = event.target.getBoundingClientRect();
    
    // Use original CT image dimensions instead of displayed image dimensions
    // imageInfo.shape is [x, y, z] format, so we need [x, y] = [width, height]
    const originalWidth = imageInfo.shape[0];   // x dimension
    const originalHeight = imageInfo.shape[1];  // y dimension
    
    const x = Math.floor((event.clientX - rect.left) * (originalWidth / rect.width));
    const y = Math.floor((event.clientY - rect.top) * (originalHeight / rect.height));
    
    console.log(`DEBUG Frontend: Click at display (${event.clientX - rect.left}, ${event.clientY - rect.top})`);
    console.log(`DEBUG Frontend: Display size (${rect.width}, ${rect.height})`);
    console.log(`DEBUG Frontend: Original CT size (${originalWidth}, ${originalHeight})`);
    console.log(`DEBUG Frontend: Calculated coordinates (${x}, ${y})`);

    try {
      const response = await axios.post('/api/interact_segment', {
        case_name: selectedCase,
        x: x,
        y: y,
        z: currentSlice,
        positive: interactionMode === 'positive'
      });

      if (response.data.success) {
        setSegmentationStats(response.data.segmentation_stats);
        showAlert(
          `${interactionMode === 'positive' ? 'Positive' : 'Negative'} point added at (${x}, ${y})`, 
          'success'
        );
        
        // Reload image to show updated segmentation
        setTimeout(() => {
          loadSliceImages();
          loadInteractionPoints();
        }, 500);
      } else {
        showAlert(`Segmentation failed: ${response.data.error}`, 'danger');
      }
    } catch (error) {
      console.error('Segmentation interaction failed:', error);
      showAlert('Segmentation interaction failed', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleClearSegmentation = async () => {
    if (!selectedCase) return;
    
    try {
      const response = await axios.post(`/api/clear_segmentation/${selectedCase}`);
      if (response.data.success) {
        setInteractionPoints([]);
        setSegmentationStats(null);
        showAlert('Segmentation cleared', 'success');
        loadSliceImages();
      }
    } catch (error) {
      console.error('Error clearing segmentation:', error);
      showAlert('Error clearing segmentation', 'danger');
    }
  };

  const handleSliceChange = (event) => {
    setCurrentSlice(parseInt(event.target.value));
  };

  return (
    <Container className="mt-4">
      {/* Header */}
      <div className="demo-info text-center mb-4">
        <h1><i className="fas fa-mouse-pointer"></i> Interactive Segmentation Viewer</h1>
        <p className="lead mb-0">Click on CT images to segment organs using nnInteractive AI</p>
      </div>

      {/* Alert */}
      {alert.show && (
        <Alert variant={alert.variant} dismissible onClose={() => setAlert({ show: false, message: '', variant: 'info' })}>
          {alert.message}
        </Alert>
      )}

      {/* Controls */}
      <Row className="mb-4">
        <Col md={6}>
          <Card>
            <Card.Header>
              <h5><i className="fas fa-cog"></i> Controls</h5>
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

              {selectedCase && (
                <>
                  <div className="mb-2">
                    <small className="text-muted">
                      Selected: <strong>{selectedCase}</strong>
                    </small>
                  </div>
                  
                  <Form.Group className="mb-3">
                    <Form.Label>
                      Slice: {currentSlice} / {maxSlice}
                    </Form.Label>
                    <Form.Range
                      min="0"
                      max={maxSlice}
                      value={currentSlice}
                      onChange={handleSliceChange}
                    />
                    <div className="d-flex justify-content-between">
                      <small className="text-muted">0</small>
                      <small className="text-muted">{maxSlice}</small>
                    </div>
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Label>Interaction Mode:</Form.Label>
                    <div>
                      <Form.Check
                        inline
                        type="radio"
                        label="Positive (include)"
                        name="interactionMode"
                        checked={interactionMode === 'positive'}
                        onChange={() => setInteractionMode('positive')}
                      />
                      <Form.Check
                        inline
                        type="radio"
                        label="Negative (exclude)"
                        name="interactionMode"
                        checked={interactionMode === 'negative'}
                        onChange={() => setInteractionMode('negative')}
                      />
                    </div>
                  </Form.Group>

                  <Button
                    variant="warning"
                    onClick={handleClearSegmentation}
                    className="w-100"
                  >
                    <i className="fas fa-eraser"></i> Clear Segmentation
                  </Button>
                </>
              )}
            </Card.Body>
          </Card>
        </Col>

        <Col md={6}>
          <Card>
            <Card.Header>
              <h5><i className="fas fa-info-circle"></i> Information</h5>
            </Card.Header>
            <Card.Body>
              {imageInfo ? (
                <div>
                  <p><strong>Image Dimensions:</strong> {imageInfo.shape.join(' × ')}</p>
                  <p><strong>Total Slices:</strong> {maxSlice + 1}</p>
                  <p><strong>Spacing:</strong> {imageInfo.spacing.map(s => s.toFixed(2)).join(' × ')} mm</p>
                  
                  {segmentationStats && (
                    <div className="mt-3">
                      <h6>Segmentation Stats:</h6>
                      <p><strong>Segmented Voxels:</strong> {segmentationStats.total_voxels.toLocaleString()}</p>
                      <p><strong>Unique Values:</strong> {segmentationStats.unique_values.join(', ')}</p>
                    </div>
                  )}
                  
                  {interactionPoints.length > 0 && (
                    <div className="mt-3">
                      <h6>Interaction Points on Slice {currentSlice}:</h6>
                      {interactionPoints.map((point, index) => (
                        <Badge 
                          key={index} 
                          bg={point.positive ? 'success' : 'danger'} 
                          className="me-1 mb-1"
                        >
                          {point.positive ? '+' : '-'} ({point.x}, {point.y})
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-muted">Select a case to view information</p>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Image Viewer */}
      {selectedCase && (
        <Row className="justify-content-center">
          <Col md={8} lg={6}>
            <Card>
              <Card.Header>
                <h5><i className="fas fa-image"></i> CT Scan with Interactive Segmentation</h5>
                <small className="text-muted">Click to add {interactionMode} points for real-time segmentation</small>
              </Card.Header>
              <Card.Body className="text-center">
                <div style={{ position: 'relative', display: 'inline-block' }}>
                  <img
                    ref={originalImageRef}
                    alt={`CT Slice ${currentSlice}`}
                    className="img-fluid"
                    style={{ 
                      maxWidth: '100%', 
                      minHeight: '400px',
                      cursor: loading ? 'wait' : 'crosshair',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      backgroundColor: '#f8f9fa'
                    }}
                    onClick={handleImageClick}
                    onError={(e) => {
                      console.error('Image load error:', e);
                      console.error('Failed URL:', e.target.src);
                      showAlert('Failed to load CT image. Check console for details.', 'danger');
                    }}
                  />
                  
                  
                  {loading && (
                    <div style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      background: 'rgba(0,0,0,0.7)',
                      color: 'white',
                      padding: '10px',
                      borderRadius: '4px'
                    }}>
                      <span className="spinner-border spinner-border-sm me-2"></span>
                      Processing...
                    </div>
                  )}
                </div>
                <div className="mt-3">
                  <div className="mb-2">
                    <Badge bg={interactionMode === 'positive' ? 'success' : 'danger'} className="me-2">
                      {interactionMode === 'positive' ? 'Positive Mode' : 'Negative Mode'}
                    </Badge>
                    <small className="text-muted">
                      Click on organs/tissues to segment them
                    </small>
                  </div>
                  {segmentationStats && (
                    <div>
                      <small className="text-success">
                        <i className="fas fa-check-circle me-1"></i>
                        Segmented {segmentationStats.total_voxels.toLocaleString()} voxels
                      </small>
                    </div>
                  )}
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Instructions */}
      <Row className="mt-4">
        <Col>
          <Card>
            <Card.Header>
              <h5><i className="fas fa-question-circle"></i> How to Use</h5>
            </Card.Header>
            <Card.Body>
              <ol>
                <li><strong>Select a Case:</strong> Choose an uploaded CT scan from the dropdown</li>
                <li><strong>Navigate Slices:</strong> Use the slider to browse through different slices</li>
                <li><strong>Choose Mode:</strong> Select "Positive" to include regions or "Negative" to exclude them</li>
                <li><strong>Click to Segment:</strong> Click on the CT image to add interaction points</li>
                <li><strong>View Results:</strong> See the segmentation mask update in real-time on the right</li>
                <li><strong>Refine:</strong> Add more points or switch modes to refine the segmentation</li>
                <li><strong>Clear:</strong> Use "Clear Segmentation" to start over</li>
              </ol>
              
              <div className="mt-3">
                <h6>Tips:</h6>
                <ul>
                  <li>Start with positive points on the organ you want to segment</li>
                  <li>Add negative points to exclude unwanted regions</li>
                  <li>The AI learns from each interaction and improves the segmentation</li>
                  <li>Different slices may require different interaction points</li>
                </ul>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default InteractiveViewer;