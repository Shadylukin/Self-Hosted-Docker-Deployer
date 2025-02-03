"""
Tests for caching utilities.
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, Any

import pytest

from easy_docker_deploy.utils.caching import cache_result, clear_cache
from easy_docker_deploy.utils.exceptions import CacheError

@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir

def test_cache_result_decorator(temp_cache_dir: Path):
    """Test the cache_result decorator."""
    counter = 0
    
    @cache_result("test_cache", cache_dir=temp_cache_dir)
    def test_function() -> Dict[str, Any]:
        nonlocal counter
        counter += 1
        return {"count": counter, "timestamp": time.time()}
    
    # First call should execute function
    result1 = test_function()
    assert result1["count"] == 1
    
    # Second call should return cached result
    result2 = test_function()
    assert result2["count"] == 1
    assert result2 == result1
    
    # Verify cache file exists
    cache_file = temp_cache_dir / "test_cache.json"
    assert cache_file.exists()
    
    # Verify cache content
    with open(cache_file) as f:
        cached_data = json.load(f)
    assert cached_data == result1

def test_cache_expiration(temp_cache_dir: Path):
    """Test cache expiration."""
    counter = 0
    
    @cache_result("test_cache", ttl=1, cache_dir=temp_cache_dir)
    def test_function() -> Dict[str, Any]:
        nonlocal counter
        counter += 1
        return {"count": counter}
    
    # First call
    result1 = test_function()
    assert result1["count"] == 1
    
    # Second call (within TTL)
    result2 = test_function()
    assert result2["count"] == 1
    
    # Wait for cache to expire
    time.sleep(1.1)
    
    # Third call (after TTL)
    result3 = test_function()
    assert result3["count"] == 2

def test_clear_cache(temp_cache_dir: Path):
    """Test cache clearing."""
    # Create some cache files
    for key in ["test1", "test2", "test3"]:
        cache_file = temp_cache_dir / f"{key}.json"
        with open(cache_file, "w") as f:
            json.dump({"key": key}, f)
    
    # Clear specific cache file
    clear_cache("test1", cache_dir=temp_cache_dir)
    assert not (temp_cache_dir / "test1.json").exists()
    assert (temp_cache_dir / "test2.json").exists()
    assert (temp_cache_dir / "test3.json").exists()
    
    # Clear all cache files
    clear_cache(cache_dir=temp_cache_dir)
    assert not (temp_cache_dir / "test2.json").exists()
    assert not (temp_cache_dir / "test3.json").exists()

@pytest.mark.skipif(os.name == "nt", reason="File permissions work differently on Windows")
def test_cache_error_handling(temp_cache_dir: Path):
    """Test error handling in cache operations."""
    # Test invalid cache directory
    nonexistent_dir = Path("/nonexistent/path/that/does/not/exist")
    with pytest.raises(CacheError):
        clear_cache(cache_dir=nonexistent_dir)
    
    # Test cache write failure
    read_only_dir = temp_cache_dir / "readonly"
    read_only_dir.mkdir()
    read_only_dir.chmod(0o444)  # Make directory read-only
    
    @cache_result("test_cache", cache_dir=read_only_dir)
    def test_function() -> Dict[str, Any]:
        return {"data": "test"}
    
    # Should still work (fallback to function call)
    result = test_function()
    assert result == {"data": "test"}
    
    # Test cache clear failure
    with pytest.raises(CacheError):
        clear_cache(cache_dir=read_only_dir)

@pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
def test_cache_error_handling_windows(temp_cache_dir: Path):
    """Test error handling in cache operations on Windows."""
    # Test invalid cache directory (use a file as directory)
    test_file = temp_cache_dir / "test.txt"
    test_file.touch()
    with pytest.raises(CacheError):
        clear_cache(cache_dir=test_file)
    
    # Test cache write failure
    # Note: Windows handles file permissions differently
    # so we'll test with a file instead of a directory
    @cache_result("test_cache", cache_dir=test_file)
    def test_function() -> Dict[str, Any]:
        return {"data": "test"}
    
    # Should still work (fallback to function call)
    result = test_function()
    assert result == {"data": "test"} 