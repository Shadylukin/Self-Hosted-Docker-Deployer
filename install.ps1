# PowerShell installation script for Easy Docker Deploy

# Clear screen and show welcome message
Clear-Host
Write-Host @"
========================================
   Easy Docker Deploy - Installation
========================================
"@ -ForegroundColor Blue

# Check if running from system32
$currentDir = Get-Location
if ($currentDir.Path -eq "C:\WINDOWS\system32") {
    Write-Host "`nERROR: Please run this script from the correct directory!" -ForegroundColor Red
    Write-Host "`nCorrect installation steps:"
    Write-Host "1. Open PowerShell as Administrator"
    Write-Host "2. Navigate to the Easy Docker Deploy directory:"
    Write-Host "   cd 'C:\path\to\Easy Docker Deploy'" -ForegroundColor Yellow
    Write-Host "3. Run the installation script:"
    Write-Host "   .\install.ps1" -ForegroundColor Yellow
    Write-Host "`nNeed help? Visit: https://github.com/yourusername/easy-docker-deploy#installation"
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path ".\src\easy_docker_deploy")) {
    Write-Host "`nERROR: Cannot find Easy Docker Deploy files!" -ForegroundColor Red
    Write-Host "Please make sure you're in the correct directory containing the source code."
    Write-Host "`nCorrect installation steps:"
    Write-Host "1. Download the code:"
    Write-Host "   git clone https://github.com/yourusername/easy-docker-deploy.git" -ForegroundColor Yellow
    Write-Host "2. Navigate to the directory:"
    Write-Host "   cd easy-docker-deploy" -ForegroundColor Yellow
    Write-Host "3. Run the installation script:"
    Write-Host "   .\install.ps1" -ForegroundColor Yellow
    exit 1
}

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "`nERROR: Administrator privileges required!" -ForegroundColor Red
    Write-Host "`nPlease follow these steps:"
    Write-Host "1. Open PowerShell as Administrator:"
    Write-Host "   - Right-click on PowerShell"
    Write-Host "   - Select 'Run as Administrator'"
    Write-Host "2. Navigate to:" -NoNewline
    Write-Host " $currentDir" -ForegroundColor Yellow
    Write-Host "3. Run:" -NoNewline
    Write-Host " .\install.ps1" -ForegroundColor Yellow
    exit 1
}

# Function to check Windows version and requirements
function Test-DockerRequirements {
    Write-Host "`nChecking system requirements for Docker..."
    
    # Check Windows version
    $osInfo = Get-WmiObject -Class Win32_OperatingSystem
    $windowsVersion = [System.Environment]::OSVersion.Version
    $isWindows10OrHigher = $windowsVersion.Major -ge 10
    $buildNumber = $windowsVersion.Build
    
    Write-Host "Operating System: " -NoNewline
    Write-Host "$($osInfo.Caption) (Build $buildNumber)" -ForegroundColor Cyan
    
    # Check if Windows 10 Pro/Enterprise/Education or Windows 11
    $edition = $osInfo.OperatingSystemSKU
    $isValidEdition = @(48,49,4,27,70,1,4,7) -contains $edition # Pro, Enterprise, Education editions
    
    if (-not $isWindows10OrHigher) {
        Write-Host "[ERROR] Docker Desktop requires Windows 10 or higher" -ForegroundColor Red
        return $false
    }
    
    if (-not $isValidEdition) {
        Write-Host "[WARNING] Docker Desktop works best with Windows Pro, Enterprise, or Education editions" -ForegroundColor Yellow
        Write-Host "You may need to install Windows Subsystem for Linux (WSL 2) manually"
        return $true
    }
    
    # Check processor architecture
    $arch = [System.Environment]::GetEnvironmentVariable("PROCESSOR_ARCHITECTURE")
    Write-Host "Processor Architecture: " -NoNewline
    Write-Host $arch -ForegroundColor Cyan
    
    if ($arch -ne "AMD64") {
        Write-Host "[ERROR] Docker Desktop requires a 64-bit processor" -ForegroundColor Red
        return $false
    }
    
    # Check available RAM
    $computerSystem = Get-WmiObject -Class Win32_ComputerSystem
    $totalRAMGB = [math]::Round($computerSystem.TotalPhysicalMemory / 1GB, 2)
    Write-Host "Available RAM: " -NoNewline
    Write-Host "$totalRAMGB GB" -ForegroundColor Cyan
    
    if ($totalRAMGB -lt 4) {
        Write-Host "[ERROR] Docker Desktop requires at least 4GB of RAM" -ForegroundColor Red
        return $false
    }
    
    # Check if Hyper-V is available
    $hyperv = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -ErrorAction SilentlyContinue
    Write-Host "Hyper-V Status: " -NoNewline
    if ($hyperv) {
        Write-Host "Available" -ForegroundColor Green
    } else {
        Write-Host "Not Available" -ForegroundColor Yellow
        Write-Host "WSL 2 will be used instead of Hyper-V"
    }
    
    return $true
}

# Function to help install Docker
function Install-Docker {
    Write-Host "`nDocker Installation Guide"
    Write-Host "========================"
    
    $requirements = Test-DockerRequirements
    if (-not $requirements) {
        Write-Host "`nYour system does not meet the minimum requirements for Docker Desktop."
        Write-Host "Please check the system requirements at:"
        Write-Host "https://docs.docker.com/desktop/windows/install/" -ForegroundColor Blue
        return $false
    }
    
    Write-Host "`nInstallation Steps:"
    
    # 1. WSL 2 Installation
    Write-Host "`n1. Installing Windows Subsystem for Linux (WSL 2)..."
    Write-Host "   Running command: " -NoNewline
    Write-Host "wsl --install" -ForegroundColor Yellow
    
    try {
        Start-Process powershell -Verb RunAs -ArgumentList "wsl --install" -Wait
        Write-Host "   [OK] WSL 2 installation initiated" -ForegroundColor Green
    } catch {
        Write-Host "   [ERROR] Failed to install WSL 2" -ForegroundColor Red
        Write-Host "   Please install WSL 2 manually: https://docs.microsoft.com/en-us/windows/wsl/install"
    }
    
    # 2. Docker Desktop Installation
    Write-Host "`n2. Downloading Docker Desktop..."
    $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    $installerPath = "$env:TEMP\DockerDesktopInstaller.exe"
    
    try {
        Invoke-WebRequest -Uri $dockerUrl -OutFile $installerPath
        Write-Host "   [OK] Docker Desktop installer downloaded" -ForegroundColor Green
        
        Write-Host "`n3. Installing Docker Desktop..."
        Write-Host "   This may take several minutes..."
        Start-Process $installerPath -Wait -ArgumentList "install --quiet"
        Write-Host "   [OK] Docker Desktop installation completed" -ForegroundColor Green
        
        Write-Host "`n4. Cleaning up..."
        Remove-Item $installerPath -Force
        Write-Host "   [OK] Installer cleaned up" -ForegroundColor Green
    } catch {
        Write-Host "   [ERROR] Failed to download or install Docker Desktop" -ForegroundColor Red
        Write-Host "   Please download and install manually from:"
        Write-Host "   https://www.docker.com/products/docker-desktop" -ForegroundColor Blue
        return $false
    }
    
    Write-Host "`nDocker Desktop installation completed!"
    Write-Host "Please follow these steps:"
    Write-Host "1. Restart your computer"
    Write-Host "2. Start Docker Desktop from the Start menu"
    Write-Host "3. Run this installation script again"
    
    return $true
}

# Check if Docker is installed and offer to install if not
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerInstalled) {
    Write-Host "`nDocker is not installed on your system." -ForegroundColor Yellow
    $installDocker = Read-Host "Would you like to install Docker Desktop now? (y/n)"
    if ($installDocker -eq 'y') {
        $success = Install-Docker
        if ($success) {
            Write-Host "`nPlease restart your computer and run this script again."
        }
        exit 0
    } else {
        Write-Host "Please install Docker Desktop manually and run this script again."
        exit 1
    }
}

# Function to check and install dependencies
function Test-Dependency {
    param (
        [string]$Name,
        [string]$Command,
        [string]$InstallGuide,
        [string]$MinVersion = $null
    )
    
    Write-Host "Checking for $Name... " -NoNewline
    try {
        $cmdInfo = Get-Command $Command -ErrorAction Stop
        if ($MinVersion) {
            $version = & $Command --version 2>&1
            if ($version -match $MinVersion) {
                Write-Host "[OK]" -ForegroundColor Green
                return $true
            } else {
                Write-Host "[UPDATE NEEDED]" -ForegroundColor Yellow
                Write-Host "Current version doesn't meet minimum requirements. $InstallGuide"
                return $false
            }
        } else {
            Write-Host "[OK]" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host "[NOT FOUND]" -ForegroundColor Red
        Write-Host $InstallGuide
        return $false
    }
}

# Check all dependencies
$dependencies = @(
    @{
        Name = "Python 3.7+"
        Command = "python"
        InstallGuide = "Download and install from: https://www.python.org/downloads/"
        MinVersion = "Python 3\.(7|8|9|1[0-9])"
    },
    @{
        Name = "pip"
        Command = "pip"
        InstallGuide = "Run: python -m ensurepip --upgrade"
    },
    @{
        Name = "Docker Desktop"
        Command = "docker"
        InstallGuide = "Download and install from: https://www.docker.com/products/docker-desktop"
    },
    @{
        Name = "Docker Compose"
        Command = "docker-compose"
        InstallGuide = "Included with Docker Desktop. Please install Docker Desktop."
    },
    @{
        Name = "Git"
        Command = "git"
        InstallGuide = "Download and install from: https://git-scm.com/downloads"
    }
)

$allDependenciesInstalled = $true
Write-Host "`nChecking system requirements..."
foreach ($dep in $dependencies) {
    if (-not (Test-Dependency @dep)) {
        $allDependenciesInstalled = $false
    }
}

if (-not $allDependenciesInstalled) {
    Write-Host "`nPlease install missing dependencies and run this script again." -ForegroundColor Red
    Write-Host "Need help? Visit: https://github.com/yourusername/easy-docker-deploy#requirements"
    exit 1
}

# Check if Docker is running
Write-Host "`nChecking Docker status... " -NoNewline
try {
    $null = docker info 2>&1
    Write-Host "[RUNNING]" -ForegroundColor Green
} catch {
    Write-Host "[NOT RUNNING]" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and run this script again."
    Write-Host "1. Open Docker Desktop"
    Write-Host "2. Wait for Docker to start"
    Write-Host "3. Run this script again"
    exit 1
}

Write-Host "`nPreparing to install Easy Docker Deploy..."

# Create virtual environment
Write-Host "Setting up Python environment... " -NoNewline
try {
    python -m venv venv 2>&1 | Out-Null
    .\venv\Scripts\Activate.ps1
    Write-Host "[OK]" -ForegroundColor Green
} catch {
    Write-Host "[FAILED]" -ForegroundColor Red
    Write-Host "Error creating Python virtual environment: $_"
    exit 1
}

# Install the package
Write-Host "Installing package... " -NoNewline
try {
    pip install typer rich click pyyaml jinja2 requests docker python-dotenv 2>&1 | Out-Null
    pip install -e . 2>&1 | Out-Null
    Write-Host "[OK]" -ForegroundColor Green
} catch {
    Write-Host "[FAILED]" -ForegroundColor Red
    Write-Host "Error installing package: $_"
    exit 1
}

# Install pytest and pytest-cov
Write-Host "Installing pytest and pytest-cov... " -NoNewline
try {
    pip install pytest pytest-cov 2>&1 | Out-Null
    Write-Host "[OK]" -ForegroundColor Green
} catch {
    Write-Host "[FAILED]" -ForegroundColor Red
    Write-Host "Error installing pytest and pytest-cov: $_"
    exit 1
}

# Run tests with coverage report
Write-Host "Running tests with coverage report... " -NoNewline
try {
    pytest --cov=src/easy_docker_deploy --cov-report=term-missing 2>&1 | Out-Null
    Write-Host "[OK]" -ForegroundColor Green
} catch {
    Write-Host "[FAILED]" -ForegroundColor Red
    Write-Host "Error running tests: $_"
    exit 1
}

# Create PowerShell profile if it doesn't exist
if (!(Test-Path $PROFILE)) {
    Write-Host "Creating PowerShell profile... " -NoNewline
    try {
        New-Item -Path $PROFILE -Type File -Force | Out-Null
        Write-Host "[OK]" -ForegroundColor Green
    } catch {
        Write-Host "[FAILED]" -ForegroundColor Red
        Write-Host "Error creating PowerShell profile: $_"
        exit 1
    }
}

# Add functions to PowerShell profile
Write-Host "Creating commands... " -NoNewline
$functions = @'

# Easy Docker Deploy functions
function global:edd {
    if ($args.Count -eq 0) {
        Write-Host "Starting Easy Docker Deploy wizard...`n"
        python -m easy_docker_deploy wizard
    } else {
        python -m easy_docker_deploy $args
    }
}
function global:edd-list { python -m easy_docker_deploy list $args }
function global:edd-deploy { python -m easy_docker_deploy deploy $args }
function global:edd-search { python -m easy_docker_deploy deploy -s $args }
'@

try {
    Add-Content -Path $PROFILE -Value $functions
    Write-Host "[OK]" -ForegroundColor Green
} catch {
    Write-Host "[FAILED]" -ForegroundColor Red
    Write-Host "Error creating commands: $_"
    exit 1
}

Write-Host @"

========================================
   Installation Complete!
========================================
"@ -ForegroundColor Green

Write-Host "`nAvailable commands:"
Write-Host "  edd" -ForegroundColor Blue -NoNewline; Write-Host " - Start the interactive deployment wizard"
Write-Host "  edd list" -ForegroundColor Blue -NoNewline; Write-Host " - List available applications"
Write-Host "  edd deploy NUMBER" -ForegroundColor Blue -NoNewline; Write-Host " - Deploy application by number"
Write-Host "  edd-search TERM" -ForegroundColor Blue -NoNewline; Write-Host " - Search and deploy applications"

Write-Host "`nRequired steps:"
Write-Host "1. " -NoNewline; Write-Host "Restart PowerShell" -ForegroundColor Yellow -NoNewline; Write-Host " or run: " -NoNewline; Write-Host ". `$PROFILE" -ForegroundColor Yellow
Write-Host "2. Run " -NoNewline; Write-Host "edd" -ForegroundColor Blue -NoNewline; Write-Host " to start the deployment wizard"

Write-Host "`nTroubleshooting:"
Write-Host "- Make sure Docker Desktop is running"
Write-Host "- Check the documentation at: https://github.com/yourusername/easy-docker-deploy"
Write-Host "- Report issues at: https://github.com/yourusername/easy-docker-deploy/issues"

Write-Host "`nTip: The wizard will guide you through selecting and deploying applications!"
