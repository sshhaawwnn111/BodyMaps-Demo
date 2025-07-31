import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Navbar, Nav, Container } from 'react-bootstrap';
import UploadPage from './components/UploadPage';
import ResultsPage from './components/ResultsPage';
import InteractiveViewer from './components/InteractiveViewer';

function App() {
  return (
    <Router>
      <div className="App">
        {/* Navigation Bar */}
        <Navbar bg="dark" variant="dark" expand="lg">
          <Container>
            <Navbar.Brand as={Link} to="/">
              <i className="fas fa-brain me-2"></i>
              BodyMaps Demo
            </Navbar.Brand>
            <Navbar.Toggle aria-controls="basic-navbar-nav" />
            <Navbar.Collapse id="basic-navbar-nav">
              <Nav className="me-auto">
                <Nav.Link as={Link} to="/">
                  <i className="fas fa-upload me-1"></i>
                  Upload & Process
                </Nav.Link>
                <Nav.Link as={Link} to="/interactive">
                  <i className="fas fa-mouse-pointer me-1"></i>
                  Interactive Viewer
                </Nav.Link>
              </Nav>
            </Navbar.Collapse>
          </Container>
        </Navbar>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/interactive" element={<InteractiveViewer />} />
          <Route path="/results/:caseName" element={<ResultsPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;