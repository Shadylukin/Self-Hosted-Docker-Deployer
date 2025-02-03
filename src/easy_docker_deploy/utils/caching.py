"""
Caching utilities for Easy Docker Deploy.
"""
import json
import time
import os
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from .exceptions import CacheError
from .logging import get_logger, log_with_context

logger = get_logger(__name__)

# Type variable for generic function type
F = TypeVar('F', bound=Callable[..., Any])

def cache_result(
    cache_key: str,
    ttl: int = 3600,  # 1 hour default
    cache_dir: Optional[Path] = None
) -> Callable[[F], F]:
    """
    Decorator to cache function results.
    
    Args:
        cache_key: Key to use for caching
        ttl: Time to live in seconds
        cache_dir: Directory to store cache files (defaults to ~/.easy-docker-deploy/cache)
        
    Returns:
        Decorated function
        
    Example:
        @cache_result('github_apps', ttl=3600)
        def fetch_applications():
            # Fetch and return applications
            pass
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get cache directory
            cache_path = cache_dir or Path.home() / ".easy-docker-deploy" / "cache"
            
            try:
                # Create cache directory if it doesn't exist
                cache_path.mkdir(parents=True, exist_ok=True)
                
                # Create cache file path
                cache_file = cache_path / f"{cache_key}.json"
                
                # Check if cache exists and is valid
                if cache_file.exists():
                    cache_age = time.time() - cache_file.stat().st_mtime
                    if cache_age < ttl:
                        logger.debug(
                            "Loading from cache",
                            **log_with_context(
                                cache_key=cache_key,
                                cache_age=cache_age
                            )
                        )
                        with open(cache_file) as f:
                            return json.load(f)
                
                # Cache miss or expired, call function
                logger.debug(
                    "Cache miss, calling function",
                    **log_with_context(cache_key=cache_key)
                )
                result = func(*args, **kwargs)
                
                # Save to cache
                with open(cache_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                logger.debug(
                    "Updated cache",
                    **log_with_context(cache_key=cache_key)
                )
                return result
                
            except Exception as e:
                logger.error(
                    "Cache operation failed",
                    **log_with_context(
                        cache_key=cache_key,
                        error=str(e)
                    )
                )
                # If cache fails, still try to return function result
                return func(*args, **kwargs)
        
        # Cast to preserve type hints
        return cast(F, wrapper)
    
    return decorator

def clear_cache(cache_key: Optional[str] = None, cache_dir: Optional[Path] = None) -> None:
    """
    Clear cached data.
    
    Args:
        cache_key: Optional specific cache key to clear
        cache_dir: Optional cache directory (defaults to ~/.easy-docker-deploy/cache)
        
    Raises:
        CacheError: If clearing cache fails
    """
    try:
        # Get cache directory
        cache_path = cache_dir or Path.home() / ".easy-docker-deploy" / "cache"
        
        # Check if path exists and is a directory
        if cache_path.exists():
            if not cache_path.is_dir():
                raise CacheError(f"Cache path exists but is not a directory: {cache_path}")
        else:
            # On Windows, check if parent directory exists
            if os.name == "nt":
                parent = cache_path.parent
                if not parent.exists() or not parent.is_dir():
                    raise CacheError(f"Parent directory does not exist or is not a directory: {parent}")
            raise CacheError(f"Cache directory does not exist: {cache_path}")
        
        if cache_key:
            # Clear specific cache file
            cache_file = cache_path / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    cache_file.unlink()
                    logger.info(
                        "Cleared cache",
                        **log_with_context(cache_key=cache_key)
                    )
                except Exception as e:
                    raise CacheError(f"Failed to delete cache file: {str(e)}")
        else:
            # Clear all cache files
            try:
                for cache_file in cache_path.glob("*.json"):
                    cache_file.unlink()
                logger.info("Cleared all cache files")
            except Exception as e:
                raise CacheError(f"Failed to clear cache files: {str(e)}")
                
    except CacheError:
        raise
    except Exception as e:
        logger.error(
            "Failed to clear cache",
            **log_with_context(
                cache_key=cache_key,
                error=str(e)
            )
        )
        raise CacheError(f"Failed to clear cache: {str(e)}") from e 