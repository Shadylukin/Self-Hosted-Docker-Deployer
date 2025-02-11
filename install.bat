@echo off
echo Welcome to Easy Docker Deploy!
echo Let's get you set up with a powerful tool for deploying self-hosted applications.
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Please run this script as Administrator
    echo Right-click the script and select "Run as administrator"
    pause
    exit /b 1
)

:: Check Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Python is not installed. Please install Python from:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check pip
pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo pip is not installed. Please install pip or run:
    echo python -m ensurepip
    pause
    exit /b 1
)

:: Check Docker
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Docker is not installed. Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

:: Check Docker Compose
docker-compose --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Docker Compose is not installed. It should be included with Docker Desktop.
    pause
    exit /b 1
)

:: Create virtual environment
echo Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

:: Install package
echo Installing Easy Docker Deploy...
pip install -e .

:: Install pytest and pytest-cov
echo Installing pytest and pytest-cov...
pip install pytest pytest-cov

:: Run tests with coverage report
echo Running tests with coverage report...
pytest --cov=src/easy_docker_deploy --cov-report=term-missing

:: Create command file
echo Creating convenient commands...
echo @echo off > edd.bat
echo venv\Scripts\activate.bat ^& python -m easy_docker_deploy wizard %%* >> edd.bat

echo Installation complete!
echo.
echo You can now use these commands:
echo   edd         - Start the interactive deployment wizard
echo   edd list    - List available applications
echo   edd deploy  - Deploy an application
echo   edd search  - Search for applications
echo.
echo Next steps:
echo 1. Add %CD% to your PATH environment variable
echo 2. Run 'edd' to start the deployment wizard
echo.
echo Tip: The wizard will guide you through selecting and deploying applications!

pause 
