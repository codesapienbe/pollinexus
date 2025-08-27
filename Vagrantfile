# -*- mode: ruby -*-
# vi: set ft=ruby :

# Pollinexus Development VM Configuration
# This Vagrantfile creates a development environment that simulates a remote server

Vagrant.configure("2") do |config|
  # Use Ubuntu 20.04 LTS as the base box
  config.vm.box = "ubuntu/focal64"
  config.vm.box_version = "20231025.0.0"
  
  # VM configuration
  config.vm.hostname = "pollinexus-dev"
  config.vm.define "pollinexus-dev"
  
  # Provider-specific configuration
  config.vm.provider "virtualbox" do |vb|
    # VM resources
    vb.memory = "4096"  # 4GB RAM
    vb.cpus = 2         # 2 CPU cores
    vb.name = "pollinexus-dev"
    
    # Enable hardware virtualization
    vb.customize ["modifyvm", :id, "--vtx-vpid", "on"]
    vb.customize ["modifyvm", :id, "--vtxux", "on"]
    
    # Network adapter settings
    vb.customize ["modifyvm", :id, "--nictype1", "virtio"]
    
    # Display settings
    vb.gui = false
    vb.customize ["modifyvm", :id, "--vram", "128"]
  end
  
  # Network configuration
  # Forward port 8000 (API) from guest to host
  config.vm.network "forwarded_port", guest: 8000, host: 8000, auto_correct: true
  # Forward port 8001 (alternative API port)
  config.vm.network "forwarded_port", guest: 8001, host: 8001, auto_correct: true
  # Forward port 5432 (PostgreSQL) if needed
  config.vm.network "forwarded_port", guest: 5432, host: 5433, auto_correct: true
  # Forward port 6379 (Redis) if needed
  config.vm.network "forwarded_port", guest: 6379, host: 6380, auto_correct: true
  
  # Private network for internal communication
  config.vm.network "private_network", ip: "192.168.56.10"
  
  # Synced folders - mount the project directory
  config.vm.synced_folder ".", "/vagrant", 
    owner: "vagrant",
    group: "vagrant",
    mount_options: ["dmode=775,fmode=664"]
  
  # Provisioning script to set up the development environment
  config.vm.provision "shell", inline: <<-SHELL
    # Update system packages
    echo "Updating system packages..."
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install essential packages
    echo "Installing essential packages..."
    sudo apt-get install -y \
      curl \
      wget \
      git \
      build-essential \
      python3 \
      python3-pip \
      python3-venv \
      python3-dev \
      libpq-dev \
      postgresql-client \
      redis-tools \
      htop \
      tree \
      vim \
      nano \
      unzip \
      software-properties-common \
      apt-transport-https \
      ca-certificates \
      gnupg \
      lsb-release
    
    # Install Python 3.12 (if not available in default repos)
    echo "Setting up Python 3.12..."
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt-get update
    sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
    
    # Set Python 3.12 as default
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
    sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1
    
    # Install uv (fast Python package manager)
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc
    
    # Install Docker (optional, for containerized development)
    echo "Installing Docker..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Add vagrant user to docker group
    sudo usermod -aG docker vagrant
    
    # Install Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Install PostgreSQL (for production-like database)
    echo "Installing PostgreSQL..."
    sudo apt-get install -y postgresql postgresql-contrib
    
    # Configure PostgreSQL
    sudo -u postgres psql -c "CREATE DATABASE pollinexus;"
    sudo -u postgres psql -c "CREATE USER pollinexus WITH ENCRYPTED PASSWORD 'pollinexus_dev';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE pollinexus TO pollinexus;"
    
    # Install Redis (for Celery broker)
    echo "Installing Redis..."
    sudo apt-get install -y redis-server
    
    # Configure Redis
    sudo sed -i 's/bind 127.0.0.1/bind 0.0.0.0/' /etc/redis/redis.conf
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
    
    # Install Node.js (for frontend development if needed)
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    
    # Install development tools
    echo "Installing development tools..."
    sudo apt-get install -y \
      pkg-config \
      libssl-dev \
      libffi-dev \
      libjpeg-dev \
      libpng-dev \
      libfreetype6-dev \
      liblcms2-dev \
      libopenjp2-7-dev \
      libtiff5-dev \
      libwebp-dev \
      libharfbuzz-dev \
      libfribidi-dev \
      libxcb1-dev
    
    # Set up environment variables
    echo "Setting up environment variables..."
    cat >> ~/.bashrc << 'EOF'
    
    # Pollinexus Development Environment
    export POLLINEXUS_ENVIRONMENT=development
    export POLLINEXUS_DEBUG=true
    export DATABASE_URL=postgresql://pollinexus:pollinexus_dev@localhost/pollinexus
    export CELERY_BROKER_URL=redis://localhost:6379/0
    export CELERY_RESULT_BACKEND=redis://localhost:6379/0
    
    # Python path
    export PYTHONPATH="/vagrant/src:$PYTHONPATH"
    
    # Aliases for convenience
    alias ll='ls -la'
    alias ..='cd ..'
    alias ...='cd ../..'
    alias pollinexus-dev='cd /vagrant && uv run uvicorn pollinexus.api.main:app --host 0.0.0.0 --port 8000 --reload'
    alias pollinexus-prod='cd /vagrant && uv run gunicorn pollinexus.api.main:app --bind 0.0.0.0:8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker'
    alias celery-worker='cd /vagrant && uv run celery -A pollinexus.tasks.celery_app worker --loglevel=info'
    alias celery-beat='cd /vagrant && uv run celery -A pollinexus.tasks.celery_app beat --loglevel=info'
EOF
    
    # Create project directory structure
    echo "Setting up project structure..."
    mkdir -p /vagrant/logs
    mkdir -p /vagrant/uploads
    mkdir -p /vagrant/data
    mkdir -p /vagrant/backups
    
    # Set proper permissions
    sudo chown -R vagrant:vagrant /vagrant
    
    # Install project dependencies (if pyproject.toml exists)
    if [ -f "/vagrant/pyproject.toml" ]; then
      echo "Installing project dependencies..."
      cd /vagrant
      uv sync --dev
    fi
    
    # Create a welcome message
    cat > /vagrant/WELCOME_VM.md << 'EOF'
    # Welcome to Pollinexus Development VM!
    
    This VM simulates a remote development environment for the Pollinexus API.
    
    ## Quick Start
    
    1. **Navigate to project directory:**
       ```bash
       cd /vagrant
       ```
    
    2. **Install dependencies (if not already done):**
       ```bash
       uv sync --dev
       ```
    
    3. **Start development server:**
       ```bash
       pollinexus-dev
       ```
       Or use the Makefile:
       ```bash
       make dev-remote
       ```
    
    4. **Access the API:**
       - API: http://localhost:8000
       - Docs: http://localhost:8000/docs
       - Health: http://localhost:8000/health
    
    ## Available Services
    
    - **PostgreSQL**: localhost:5433 (guest:5432)
    - **Redis**: localhost:6380 (guest:6379)
    - **API Server**: localhost:8000 (guest:8000)
    
    ## Useful Commands
    
    - `pollinexus-dev` - Start development server
    - `pollinexus-prod` - Start production server
    - `celery-worker` - Start Celery worker
    - `celery-beat` - Start Celery beat scheduler
    - `make help` - Show all available commands
    
    ## Environment Variables
    
    The following environment variables are pre-configured:
    - `POLLINEXUS_ENVIRONMENT=development`
    - `DATABASE_URL=postgresql://pollinexus:pollinexus_dev@localhost/pollinexus`
    - `CELERY_BROKER_URL=redis://localhost:6379/0`
    
    ## Troubleshooting
    
    - If services don't start, check if they're running:
      ```bash
      sudo systemctl status postgresql
      sudo systemctl status redis-server
      ```
    
    - To restart services:
      ```bash
      sudo systemctl restart postgresql
      sudo systemctl restart redis-server
      ```
    
    Happy coding! 🚀
EOF
    
    # Set up log rotation
    echo "Setting up log rotation..."
    sudo tee /etc/logrotate.d/pollinexus << 'EOF'
    /vagrant/logs/*.log {
        daily
        rotate 30
        compress
        delaycompress
        missingok
        notifempty
        copytruncate
        create 644 vagrant vagrant
    }
EOF
    
    # Create systemd service for auto-start (optional)
    echo "Setting up auto-start service..."
    sudo tee /etc/systemd/system/pollinexus-dev.service << 'EOF'
    [Unit]
    Description=Pollinexus Development Server
    After=network.target postgresql.service redis-server.service
    
    [Service]
    Type=simple
    User=vagrant
    WorkingDirectory=/vagrant
    Environment=PATH=/home/vagrant/.cargo/bin:/usr/local/bin:/usr/bin:/bin
    ExecStart=/home/vagrant/.cargo/bin/uv run uvicorn pollinexus.api.main:app --host 0.0.0.0 --port 8000 --reload
    Restart=always
    RestartSec=10
    
    [Install]
    WantedBy=multi-user.target
EOF
    
    # Enable services
    sudo systemctl enable postgresql
    sudo systemctl enable redis-server
    
    # Start services
    sudo systemctl start postgresql
    sudo systemctl start redis-server
    
    echo "VM setup complete! 🎉"
    echo "You can now SSH into the VM with: vagrant ssh"
    echo "The API will be available at: http://localhost:8000"
    
  SHELL
  
  # Post-up message
  config.vm.post_up_message = <<-SHELL
    ========================================
    Pollinexus Development VM is ready!
    ========================================
    
    SSH into the VM:
      vagrant ssh
    
    Access the API:
      http://localhost:8000
    
    API Documentation:
      http://localhost:8000/docs
    
    Health Check:
      http://localhost:8000/health
    
    Quick Start:
      vagrant ssh -c "cd /vagrant && make dev-remote"
    
    ========================================
  SHELL
  
end 