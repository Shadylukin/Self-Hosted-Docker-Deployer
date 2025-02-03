"""
Tests for the parser module.
"""
import pytest
from easy_docker_deploy.parser.markdown_parser import MarkdownParser
from easy_docker_deploy.parser.github_parser import GithubParser, Application

def test_category_extraction():
    """Test category pattern matching."""
    content = """
### Category 1
Some content
### [Category 2]
More content
### Category 3
    """
    categories = MarkdownParser.extract_categories(content)
    assert "Category 1" in categories
    assert "Category 2" in categories
    assert "Category 3" in categories

def test_application_line_parsing():
    """Test application line pattern matching."""
    # Test basic application line
    line = "- [App Name](https://example.com) - A description. `Python` [MIT]"
    result = MarkdownParser.parse_application_line(line)
    assert result is not None
    name, url, desc, lang, license = result
    assert name == "App Name"
    assert url == "https://example.com"
    assert desc == "A description"
    assert lang == "Python"
    assert license == "MIT"
    
    # Test line without language and license
    line = "- [Simple App](https://example.com) - Just a description."
    result = MarkdownParser.parse_application_line(line)
    assert result is not None
    name, url, desc, lang, license = result
    assert name == "Simple App"
    assert url == "https://example.com"
    assert desc == "Just a description"
    assert lang is None
    assert license is None

def test_docker_url_detection():
    """Test Docker URL detection."""
    # Test Docker Hub URL
    desc = "App with Docker image at hub.docker.com/r/user/app"
    url = "https://example.com"
    docker_url = MarkdownParser.extract_docker_url(desc, url)
    assert docker_url == "https://hub.docker.com/r/user/app"
    
    # Test Docker-related main URL
    desc = "Simple description"
    url = "https://github.com/user/app/dockerfile"
    docker_url = MarkdownParser.extract_docker_url(desc, url)
    assert docker_url == url

def test_github_parser_integration():
    """Test the complete GitHub parser with sample content."""
    sample_content = """
### [Category 1]
- [App 1](https://app1.com) - Description 1. `Python` [MIT]
- [App 2](https://app2.com) - Description 2 with Docker (hub.docker.com/r/user/app2).

### Category 2
- [App 3](https://app3.com/dockerfile) - Description 3. `Go` [Apache]
"""
    
    parser = GithubParser()
    apps = parser.parse_content(sample_content)
    
    # Check if all apps were parsed
    assert len(apps) == 3
    
    # Check specific application details
    app1 = apps["App 1"]
    assert app1.name == "App 1"
    assert app1.language == "Python"
    assert app1.license_type == "MIT"
    assert not app1.docker_available
    
    app2 = apps["App 2"]
    assert app2.docker_available
    assert app2.docker_url == "https://hub.docker.com/r/user/app2"
    
    app3 = apps["App 3"]
    assert app3.docker_available
    assert app3.docker_url == "https://app3.com/dockerfile"
    assert app3.language == "Go"
    
    # Test search functionality
    python_apps = parser.search_applications("python")
    assert len(python_apps) == 1
    assert python_apps[0].name == "App 1"
    
    # Test category filtering
    cat1_apps = parser.get_applications_by_category("Category 1")
    assert len(cat1_apps) == 2
    
    # Test Docker-ready filtering
    docker_apps = parser.get_docker_ready_applications()
    assert len(docker_apps) == 2 