"""
Tests for validation utilities.
"""
import os
import pytest
from pathlib import Path

from easy_docker_deploy.utils.validation import (
    validate_docker_url,
    validate_port_mapping,
    validate_volume_mapping,
    validate_environment_vars,
    validate_application_name
)
from easy_docker_deploy.utils.exceptions import ValidationError

# Docker URL test cases
docker_url_test_cases = [
    # Valid URLs
    ("nginx", "docker.io/library/nginx:latest"),
    ("user/app", "docker.io/user/app:latest"),
    ("registry.example.com/user/app", "registry.example.com/user/app:latest"),
    ("nginx:1.19", "docker.io/library/nginx:1.19"),
    # Invalid URLs
    pytest.param("", None, marks=pytest.mark.xfail(raises=ValidationError)),
    pytest.param("invalid/url/format", None, marks=pytest.mark.xfail(raises=ValidationError)),
]

@pytest.mark.parametrize("input_url,expected", docker_url_test_cases)
def test_validate_docker_url(input_url, expected):
    """Test Docker URL validation with various inputs."""
    assert validate_docker_url(input_url) == expected

# Port mapping test cases
port_mapping_test_cases = [
    # Valid mappings
    (80, "80:80"),
    ("8080:80", "8080:80"),
    # Invalid mappings
    pytest.param(0, None, marks=pytest.mark.xfail(raises=ValidationError)),
    pytest.param(65536, None, marks=pytest.mark.xfail(raises=ValidationError)),
    pytest.param("invalid", None, marks=pytest.mark.xfail(raises=ValidationError)),
    pytest.param("80:65536", None, marks=pytest.mark.xfail(raises=ValidationError)),
]

@pytest.mark.parametrize("input_port,expected", port_mapping_test_cases)
def test_validate_port_mapping(input_port, expected):
    """Test port mapping validation with various inputs."""
    assert validate_port_mapping(input_port) == expected

# Windows volume mapping test cases
@pytest.mark.skipif(os.name != "nt", reason="Windows paths need different handling")
@pytest.mark.parametrize("input_volume,expected_error", [
    # Valid mappings handled in separate test
    ("invalid:/data", "Invalid Windows path"),
    ("C:", "Invalid volume mapping format"),
    ("C:invalid", "Invalid Windows path"),
    ("C:/path1:C:/path2", "Container path cannot be a Windows path"),
    ("C:/path1:C:/path2:path3", "Invalid container path"),
])
def test_validate_volume_mapping_windows_errors(input_volume, expected_error):
    """Test volume mapping validation errors on Windows."""
    with pytest.raises(ValidationError, match=expected_error):
        validate_volume_mapping(input_volume)

@pytest.mark.skipif(os.name != "nt", reason="Windows paths need different handling")
def test_validate_volume_mapping_windows_valid():
    """Test valid volume mappings on Windows."""
    test_path = Path("C:/test/path").resolve()
    assert validate_volume_mapping(test_path) == f"{test_path}:/data"
    assert validate_volume_mapping("C:/test/path:/data") == f"{test_path}:/data"
    assert validate_volume_mapping(None) is None

# Unix volume mapping test cases
@pytest.mark.skipif(os.name == "nt", reason="Unix paths need different handling")
@pytest.mark.parametrize("input_volume,expected_error", [
    ("invalid", "Invalid volume mapping format"),
    ("/path1:/path2:", "Invalid volume mapping format"),
    (":/data", "Invalid host path"),
])
def test_validate_volume_mapping_unix_errors(input_volume, expected_error):
    """Test volume mapping validation errors on Unix."""
    with pytest.raises(ValidationError, match=expected_error):
        validate_volume_mapping(input_volume)

@pytest.mark.skipif(os.name == "nt", reason="Unix paths need different handling")
def test_validate_volume_mapping_unix_valid():
    """Test valid volume mappings on Unix."""
    test_path = Path("/test/path").resolve()
    assert validate_volume_mapping(test_path) == f"{test_path}:/data"
    assert validate_volume_mapping("/test/path:/data") == f"{test_path}:/data"
    assert validate_volume_mapping(None) is None

# Environment variables test cases
env_var_test_cases = [
    # Valid variables
    ({"KEY": "value"}, {"KEY": "value"}),
    ({"MY_VAR_1": "123"}, {"MY_VAR_1": "123"}),
    # Invalid variables
    pytest.param({"1invalid": "value"}, None, marks=pytest.mark.xfail(raises=ValidationError)),
    pytest.param({"invalid@": "value"}, None, marks=pytest.mark.xfail(raises=ValidationError)),
]

@pytest.mark.parametrize("input_vars,expected", env_var_test_cases)
def test_validate_environment_vars(input_vars, expected):
    """Test environment variables validation with various inputs."""
    assert validate_environment_vars(input_vars) == expected

# Application name test cases
app_name_test_cases = [
    # Valid names
    ("my-app", "my-app"),
    ("MY_APP", "my-app"),
    ("My App 123", "my-app-123"),
    # Invalid names
    pytest.param("", None, marks=pytest.mark.xfail(raises=ValidationError)),
    pytest.param(" ", None, marks=pytest.mark.xfail(raises=ValidationError)),
]

@pytest.mark.parametrize("input_name,expected", app_name_test_cases)
def test_validate_application_name(input_name, expected):
    """Test application name validation with various inputs."""
    assert validate_application_name(input_name) == expected 