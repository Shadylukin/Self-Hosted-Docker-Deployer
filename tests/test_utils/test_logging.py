"""
Tests for logging utilities.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any

import pytest

from easy_docker_deploy.utils.logging import (
    setup_logging,
    get_logger,
    log_with_context,
    StructuredFormatter,
    StructuredLogger
)

@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Path:
    """Create a temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir

def test_structured_formatter():
    """Test structured formatter output."""
    formatter = StructuredFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    # Add extra fields
    setattr(record, "extra_fields", {"user": "test", "action": "login"})
    
    # Format record
    output = formatter.format(record)
    data = json.loads(output)
    
    # Verify structure
    assert "timestamp" in data
    assert data["level"] == "INFO"
    assert data["logger"] == "test"
    assert data["message"] == "Test message"
    assert data["user"] == "test"
    assert data["action"] == "login"

def test_structured_logger():
    """Test structured logger functionality."""
    logger = StructuredLogger("test")
    logger.setLevel(logging.INFO)
    
    # Create a memory handler to capture logs
    class MemoryHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.records = []
            
        def emit(self, record):
            self.records.append(record)
    
    handler = MemoryHandler()
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    
    # Test logging with context
    logger.info("Test message", user="test", action="login")
    
    # Verify record
    assert len(handler.records) == 1
    record = handler.records[0]
    assert record.msg == "Test message"
    assert hasattr(record, "extra_fields")
    assert record.extra_fields == {"user": "test", "action": "login"}

def test_setup_logging(temp_log_dir: Path):
    """Test logging setup."""
    log_file = temp_log_dir / "test.log"
    
    # Setup logging
    setup_logging(
        log_level="DEBUG",
        log_file=log_file,
        structured=True,
        console=False
    )
    
    # Get logger and log some messages
    logger = get_logger("test")
    logger.debug("Debug message")
    logger.info("Info message", **log_with_context(test="value"))
    logger.warning("Warning message")
    
    # Verify log file exists and contains logs
    assert log_file.exists()
    
    # Read and parse log lines
    with open(log_file) as f:
        logs = [json.loads(line) for line in f]
    
    # Verify log contents
    assert len(logs) >= 3
    assert any(log["message"] == "Debug message" for log in logs)
    assert any(
        log["message"] == "Info message" and log.get("test") == "value"
        for log in logs
    )
    assert any(log["message"] == "Warning message" for log in logs)

def test_log_rotation(temp_log_dir: Path):
    """Test log file rotation."""
    log_file = temp_log_dir / "test.log"
    
    # Setup logging with small max size
    setup_logging(
        log_level="DEBUG",
        log_file=log_file,
        max_size=100,  # Small size to trigger rotation
        backup_count=2,
        console=False
    )
    
    logger = get_logger("test")
    
    # Write enough logs to trigger rotation
    for i in range(100):
        logger.info("Test message " * 10)  # Long message
    
    # Verify rotation
    assert log_file.exists()
    assert (temp_log_dir / "test.log.1").exists()
    assert (temp_log_dir / "test.log.2").exists()
    assert not (temp_log_dir / "test.log.3").exists()  # Should not exist

def test_log_with_context():
    """Test log context creation."""
    # Test with simple values
    context = log_with_context(user="test", count=42, active=True)
    assert isinstance(context, dict)
    assert "extra" in context
    assert "extra_fields" in context["extra"]
    assert context["extra"]["extra_fields"] == {
        "user": "test",
        "count": 42,
        "active": True
    }
    
    # Test with nested structures
    nested = log_with_context(
        data={"key": "value"},
        list=[1, 2, 3],
        none=None
    )
    assert nested["extra"]["extra_fields"]["data"] == {"key": "value"}
    assert nested["extra"]["extra_fields"]["list"] == [1, 2, 3]
    assert nested["extra"]["extra_fields"]["none"] is None 