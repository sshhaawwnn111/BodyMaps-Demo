#!/bin/bash

# BodyMaps Demo Setup Script
# This script sets up the complete environment for the BodyMaps SuPreM segmentation demo

set -e  # Exit on any error

echo "🚀 Setting up BodyMaps SuPreM Segmentation Demo..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3 is installed
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python 3 found: $PYTHON_VERSION"
        
        # Check if python3-venv is available (required on Ubuntu/Debian)
        if ! python3 -m venv --help &> /dev/null; then
            print_warning "python3-venv module not found"
            
            # Check if we're on Ubuntu/Debian
            if command -v apt &> /dev/null; then
                print_status "Installing required Python packages..."
                if sudo apt update && sudo apt install -y python3-venv python3-dev python3-pip build-essential; then
                    print_success "Required Python packages installed successfully"
                else
                    print_error "Failed to install required packages"
                    echo "Please run: sudo apt install python3-venv python3-dev python3-pip build-essential"
                    exit 1
                fi
            else
                print_error "python3-venv is required but not available."
                echo "Please install the python3-venv package for your system."
                exit 1
            fi
        else
            # Even if venv is available, check for development headers on Ubuntu/Debian
            if command -v apt &> /dev/null; then
                if ! dpkg -l | grep -q python3-dev; then
                    print_status "Installing Python development headers..."
                    if sudo apt update && sudo apt install -y python3-dev build-essential; then
                        print_success "Python development headers installed"
                    else
                        print_warning "Could not install development headers - some packages may fail to build"
                    fi
                fi
            fi
        fi
    else
        print_error "Python 3 is required but not installed."
        echo "Please install Python 3.8+ and try again."
        exit 1
    fi
}

# Check if Docker is installed and running
check_docker() {
    if command -v docker &> /dev/null; then
        print_success "Docker found"
        
        # Check if Docker daemon is running
        if docker info &> /dev/null; then
            print_success "Docker daemon is running"
        else
            print_warning "Docker is installed but not running"
            echo "Please start Docker Desktop and try again."
            exit 1
        fi
    else
        print_error "Docker is required but not installed."
        echo "Please install Docker Desktop and try again."
        echo "Visit: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
}

# Create virtual environment
setup_venv() {
    print_status "Creating Python virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip and install essential build tools
    print_status "Upgrading pip and installing build tools..."
    pip install --upgrade pip setuptools wheel
    
    print_success "Virtual environment created and activated"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Make sure we're in the virtual environment
    source venv/bin/activate
    
    # Check Python version and adjust numpy version for compatibility
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    
    if [[ "$PYTHON_VERSION" == "3.12" ]]; then
        print_warning "Python 3.12 detected - using compatible package versions"
        
        # Create a temporary requirements file with compatible versions
        cat > requirements_temp.txt << 'EOF'
Flask>=2.3.3
Werkzeug>=2.3.7
nibabel>=5.1.0
matplotlib>=3.7.2
numpy>=1.26.0
Pillow>=10.0.1
EOF
        
        # Install from the temporary requirements file
        pip install -r requirements_temp.txt
        
        # Clean up temporary file
        rm requirements_temp.txt
    else
        # Use original requirements for older Python versions
        pip install -r requirements.txt
    fi
    
    print_success "Python dependencies installed"
}

# Create required directories
create_directories() {
    print_status "Creating required directories..."
    
    mkdir -p inputs_data
    mkdir -p outputs_data
    mkdir -p static/results
    mkdir -p utils
    
    print_success "Directories created"
}

# Download SuPreM Docker image
download_suprem() {
    print_status "Checking for SuPreM Docker image..."
    
    if docker images | grep -q "qchen99/suprem"; then
        print_success "SuPreM Docker image already exists"
    else
        print_status "Downloading SuPreM Docker image (this may take 10-20 minutes)..."
        print_warning "The image is approximately 5GB in size"
        
        if docker pull qchen99/suprem:v1; then
            print_success "SuPreM Docker image downloaded successfully"
        else
            print_error "Failed to download SuPreM Docker image"
            echo "You can try downloading it manually later with:"
            echo "docker pull qchen99/suprem:v1"
        fi
    fi
}

# Check system resources
check_resources() {
    print_status "Checking system resources..."
    
    # Check available memory (cross-platform)
    if [ -f /proc/meminfo ]; then
        # Linux
        TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        TOTAL_MEM_GB=$((TOTAL_MEM_KB / 1024 / 1024))
        
        if [ $TOTAL_MEM_GB -lt 8 ]; then
            print_warning "System has ${TOTAL_MEM_GB}GB RAM. 8GB+ recommended for optimal performance."
        else
            print_success "System has ${TOTAL_MEM_GB}GB RAM"
        fi
    elif command -v sysctl &> /dev/null && sysctl -n hw.memsize &> /dev/null; then
        # macOS
        TOTAL_MEM=$(sysctl -n hw.memsize)
        TOTAL_MEM_GB=$((TOTAL_MEM / 1024 / 1024 / 1024))
        
        if [ $TOTAL_MEM_GB -lt 8 ]; then
            print_warning "System has ${TOTAL_MEM_GB}GB RAM. 8GB+ recommended for optimal performance."
        else
            print_success "System has ${TOTAL_MEM_GB}GB RAM"
        fi
    else
        print_warning "Could not determine system memory"
    fi
    
    # Check for GPU (NVIDIA)
    if command -v nvidia-smi &> /dev/null; then
        print_success "NVIDIA GPU detected"
    else
        print_warning "No NVIDIA GPU detected. Processing will use CPU (slower)."
    fi
}

# Create run script
create_run_script() {
    print_status "Creating run script..."
    
    cat > run_demo.sh << 'EOF'
#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development

# Run the application
echo "🚀 Starting BodyMaps Demo..."
echo "📱 Open your browser to: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

python app.py
EOF

    chmod +x run_demo.sh
    print_success "Run script created: ./run_demo.sh"
}

# Main setup function
main() {
    echo "=================================="
    echo "  BodyMaps Demo Setup Script"
    echo "=================================="
    echo ""
    
    # Run all checks and setup steps
    check_python
    check_docker
    check_resources
    setup_venv
    install_dependencies
    create_directories
    create_run_script
    
    echo ""
    echo "=================================="
    print_success "Setup completed successfully!"
    echo "=================================="
    echo ""
    echo "📋 Next steps:"
    echo "1. Optionally download SuPreM model: docker pull qchen99/suprem:v1"
    echo "2. Run the demo: ./run_demo.sh"
    echo "3. Open browser to: http://localhost:5000"
    echo ""
    echo "📖 For detailed instructions, see README.md"
    echo ""
    
    # Ask if user wants to download SuPreM now
    read -p "Would you like to download the SuPreM Docker image now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        download_suprem
    else
        print_warning "Skipping SuPreM download. You can download it later with:"
        echo "docker pull qchen99/suprem:v1"
    fi
    
    echo ""
    print_success "Setup complete! Run './run_demo.sh' to start the demo."
}

# Run main function
main
