import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Modal, Alert } from 'react-bootstrap';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const ResultsPage = () => {
  const { caseName } = useParams();
  const navigate = useNavigate();
  const [images, setImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [alert, setAlert] = useState({ show: false, message: '', variant: 'info' });

  useEffect(() => {
    loadResults();
  }, [caseName]);

  const loadResults = async () => {
    try {
      // Since we don't have a direct API for images, we'll construct the expected image paths
      // This mimics the original template behavior
      const mockImages = [
        `results/${caseName}/liver_slice_050.png`,
        `results/${caseName}/kidney_left_slice_050.png`,
        `results/${caseName}/kidney_right_slice_050.png`,
        `results/${caseName}/combined_labels_slice_050.png`,
        `results/${caseName}/liver_slice_052.png`,
        `results/${caseName}/kidney_left_slice_052.png`,
        `results/${caseName}/kidney_right_slice_052.png`,
        `results/${caseName}/combined_labels_slice_052.png`
      ];
      setImages(mockImages);
    } catch (error) {
      showAlert('Error loading results', 'danger');
    }
  };

  const showAlert = (message, variant = 'info') => {
    setAlert({ show: true, message, variant });
    setTimeout(() => setAlert({ show: false, message: '', variant: 'info' }), 5000);
  };

  const handleImageClick = (imagePath) => {
    setSelectedImage(imagePath);
    setShowModal(true);
  };

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const response = await axios.get(`/api/download/${caseName}`, {
        responseType: 'blob'
      });
      
      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${caseName}_results.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      showAlert('Download started successfully!', 'success');
    } catch (error) {
      showAlert('Download failed', 'danger');
    } finally {
      setDownloading(false);
    }
  };

  const getImageTitle = (imagePath) => {
    const filename = imagePath.split('/').pop();
    if (filename.includes('liver')) return 'Liver Segmentation';
    if (filename.includes('kidney_left')) return 'Left Kidney Segmentation';
    if (filename.includes('kidney_right')) return 'Right Kidney Segmentation';
    if (filename.includes('combined_labels')) return 'Combined Segmentation';
    return 'Segmentation Result';
  };

  const getImageIcon = (imagePath) => {
    if (imagePath.includes('liver')) return 'fas fa-liver';
    if (imagePath.includes('kidney')) return 'fas fa-kidneys';
    if (imagePath.includes('combined')) return 'fas fa-layer-group';
    return 'fas fa-image';
  };

  return (
    <Container className="mt-5">
      {/* Header */}
      <div className="result-header text-center">
        <h1><i className="fas fa-check-circle"></i> Segmentation Results</h1>
        <h3>Case: {caseName}</h3>
        <p className="lead mb-0">AI-powered organ segmentation completed successfully</p>
      </div>

      {/* Alert */}
      {alert.show && (
        <Alert variant={alert.variant} dismissible onClose={() => setAlert({ show: false, message: '', variant: 'info' })}>
          {alert.message}
        </Alert>
      )}

      {/* Action Buttons */}
      <Row className="mb-4">
        <Col className="text-center">
          <Button
            variant="primary"
            size="lg"
            onClick={handleDownload}
            disabled={downloading}
            className="me-3"
          >
            {downloading ? (
              <>
                <span className="spinner-border spinner-border-sm me-2"></span>
                Downloading...
              </>
            ) : (
              <>
                <i className="fas fa-download me-2"></i>
                Download Results (ZIP)
              </>
            )}
          </Button>
          <Button
            variant="outline-secondary"
            size="lg"
            onClick={() => navigate('/')}
          >
            <i className="fas fa-arrow-left me-2"></i>
            Back to Upload
          </Button>
        </Col>
      </Row>

      {/* Results Summary */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="text-center h-100">
            <Card.Body>
              <i className="fas fa-liver fa-3x text-danger mb-3"></i>
              <h5>Liver</h5>
              <p className="text-muted">Segmented successfully</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center h-100">
            <Card.Body>
              <i className="fas fa-kidneys fa-3x text-info mb-3"></i>
              <h5>Left Kidney</h5>
              <p className="text-muted">Segmented successfully</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center h-100">
            <Card.Body>
              <i className="fas fa-kidneys fa-3x text-warning mb-3"></i>
              <h5>Right Kidney</h5>
              <p className="text-muted">Segmented successfully</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center h-100">
            <Card.Body>
              <i className="fas fa-layer-group fa-3x text-success mb-3"></i>
              <h5>Combined</h5>
              <p className="text-muted">All organs together</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Image Gallery */}
      <Card>
        <Card.Header>
          <h4><i className="fas fa-images"></i> Segmentation Preview</h4>
          <small className="text-muted">Click on any image to view in full size</small>
        </Card.Header>
        <Card.Body>
          {images.length === 0 ? (
            <div className="text-center py-5">
              <i className="fas fa-image fa-3x text-muted mb-3"></i>
              <p className="text-muted">No preview images available</p>
            </div>
          ) : (
            <div className="image-gallery">
              {images.map((imagePath, index) => (
                <div key={index} className="image-item">
                  <Card className="h-100">
                    <div style={{ position: 'relative', overflow: 'hidden' }}>
                      <Card.Img
                        variant="top"
                        src={`/static/${imagePath}`}
                        alt={getImageTitle(imagePath)}
                        style={{ 
                          height: '200px', 
                          objectFit: 'cover',
                          cursor: 'pointer',
                          transition: 'transform 0.3s ease'
                        }}
                        onClick={() => handleImageClick(imagePath)}
                        onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
                        onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
                        onError={(e) => {
                          e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIG5vdCBmb3VuZDwvdGV4dD48L3N2Zz4=';
                        }}
                      />
                      <div style={{
                        position: 'absolute',
                        top: '10px',
                        right: '10px',
                        background: 'rgba(0,0,0,0.7)',
                        color: 'white',
                        padding: '5px 10px',
                        borderRadius: '15px',
                        fontSize: '12px'
                      }}>
                        <i className={getImageIcon(imagePath)}></i>
                      </div>
                    </div>
                    <Card.Body className="p-2">
                      <Card.Title style={{ fontSize: '14px', margin: 0 }}>
                        {getImageTitle(imagePath)}
                      </Card.Title>
                      <Card.Text style={{ fontSize: '12px', color: '#666', margin: 0 }}>
                        Slice {imagePath.includes('050') ? '50' : '52'}
                      </Card.Text>
                    </Card.Body>
                  </Card>
                </div>
              ))}
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Technical Details */}
      <Row className="mt-4">
        <Col md={6}>
          <Card>
            <Card.Header>
              <h5><i className="fas fa-info-circle"></i> Processing Details</h5>
            </Card.Header>
            <Card.Body>
              <ul className="list-unstyled">
                <li><strong>Model:</strong> SuPreM v1.0</li>
                <li><strong>Processing Time:</strong> ~5-15 minutes</li>
                <li><strong>Output Format:</strong> NIfTI (.nii.gz)</li>
                <li><strong>Segmented Organs:</strong> Liver, Kidneys</li>
              </ul>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Header>
              <h5><i className="fas fa-download"></i> Available Downloads</h5>
            </Card.Header>
            <Card.Body>
              <ul className="list-unstyled">
                <li><i className="fas fa-file-archive text-primary"></i> Complete results (ZIP)</li>
                <li><i className="fas fa-file-medical text-success"></i> Individual organ files</li>
                <li><i className="fas fa-layer-group text-info"></i> Combined segmentation</li>
                <li><i className="fas fa-image text-warning"></i> Preview images</li>
              </ul>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Image Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg" centered>
        <Modal.Header closeButton>
          <Modal.Title>{getImageTitle(selectedImage)}</Modal.Title>
        </Modal.Header>
        <Modal.Body className="text-center">
          {selectedImage && (
            <img
              src={`/static/${selectedImage}`}
              alt={getImageTitle(selectedImage)}
              className="img-fluid"
              style={{ maxHeight: '70vh' }}
            />
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default ResultsPage;