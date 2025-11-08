"""Tests for repository tools and URL validation"""
import pytest
from codebase_genius.python_helpers.repo_tools import validate_repo_url, find_important_files


class TestURLValidation:
    """Test repository URL validation"""
    
    def test_valid_github_url(self):
        """Test valid GitHub URL"""
        result = validate_repo_url("https://github.com/user/repo")
        assert result["valid"] is True
        assert result["normalized_url"] == "https://github.com/user/repo"
    
    def test_valid_github_url_with_git_extension(self):
        """Test GitHub URL with .git extension"""
        result = validate_repo_url("https://github.com/user/repo.git")
        assert result["valid"] is True
        assert result["normalized_url"] == "https://github.com/user/repo"
    
    def test_valid_gitlab_url(self):
        """Test valid GitLab URL"""
        result = validate_repo_url("https://gitlab.com/user/repo")
        assert result["valid"] is True
        assert "gitlab.com" in result["normalized_url"]
    
    def test_valid_bitbucket_url(self):
        """Test valid Bitbucket URL"""
        result = validate_repo_url("https://bitbucket.org/user/repo")
        assert result["valid"] is True
        assert "bitbucket.org" in result["normalized_url"]
    
    def test_invalid_url_format(self):
        """Test invalid URL format"""
        result = validate_repo_url("not-a-url")
        assert result["valid"] is False
        assert result["error"] is not None
    
    def test_unsupported_host(self):
        """Test unsupported Git host"""
        result = validate_repo_url("https://example.com/user/repo")
        assert result["valid"] is False
        assert "supported" in result["error"].lower()
    
    def test_missing_owner_or_repo(self):
        """Test URL without owner/repo"""
        result = validate_repo_url("https://github.com/user")
        assert result["valid"] is False


class TestFileDiscovery:
    """Test important file discovery"""
    
    def test_find_python_entry_points(self):
        """Test finding Python entry point files"""
        file_tree = {
            "path": "/test",
            "name": "test",
            "children": [
                {"name": "main.py", "type": "file", "path": "main.py"},
                {"name": "app.py", "type": "file", "path": "app.py"},
                {"name": "random.py", "type": "file", "path": "random.py"}
            ]
        }
        
        important = find_important_files(file_tree)
        # Should find main.py and app.py, but not random.py
        assert "main.py" in important
        assert "app.py" in important
        assert "random.py" not in important
    
    def test_find_init_files(self):
        """Test finding __init__.py files"""
        file_tree = {
            "path": "test",
            "name": "test",
            "type": "dir",
            "children": [
                {
                    "name": "package",
                    "type": "dir",
                    "path": "package",
                    "children": [
                        {"name": "__init__.py", "type": "file", "path": "package/__init__.py"}
                    ]
                }
            ]
        }
        
        important = find_important_files(file_tree)
        assert "package/__init__.py" in important
        assert any("__init__.py" in f for f in important)
    
    def test_find_priority_files_only(self):
        """Test that only priority entry points are found, not config files"""
        file_tree = {
            "path": "test",
            "name": "test",
            "type": "dir",
            "children": [
                {"name": "cli.py", "type": "file", "path": "cli.py"},
                {"name": "server.py", "type": "file", "path": "server.py"},
                {"name": "requirements.txt", "type": "file", "path": "requirements.txt"},
                {"name": "pyproject.toml", "type": "file", "path": "pyproject.toml"}
            ]
        }
        
        important = find_important_files(file_tree)
        # Should find priority Python files
        assert "cli.py" in important
        assert "server.py" in important
        # Should NOT find config files
        assert "requirements.txt" not in important
        assert "pyproject.toml" not in important
    
    def test_empty_tree(self):
        """Test empty file tree"""
        file_tree = {"path": "/test", "name": "test", "children": []}
        important = find_important_files(file_tree)
        assert important == []
