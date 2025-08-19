"""
Security tests for path traversal protection
Tests critical security vulnerabilities in file operations
"""

import os
import tempfile
import pytest
from pathlib import Path

from core.security import SecureFileHandler, SecurityError


class TestPathTraversalProtection:
    """Test protection against path traversal attacks"""

    @pytest.fixture
    def temp_safe_dir(self):
        """Create temporary safe directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            safe_dir = os.path.join(temp_dir, "safe")
            os.makedirs(safe_dir)
            
            # Create test file in safe directory
            test_file = os.path.join(safe_dir, "test.md")
            with open(test_file, 'w') as f:
                f.write("# Test Content\n- Item 1\n- Item 2")
            
            yield safe_dir

    def test_basic_path_validation_success(self, temp_safe_dir):
        """Test that valid paths are accepted"""
        test_file = os.path.join(temp_safe_dir, "test.md")
        
        # Should work without allowed_base_dirs
        validated = SecureFileHandler.validate_file_path(test_file)
        assert os.path.exists(validated)
        
        # Should work with allowed_base_dirs
        validated = SecureFileHandler.validate_file_path(test_file, {temp_safe_dir})
        assert os.path.exists(validated)

    def test_path_traversal_attacks_blocked(self, temp_safe_dir):
        """Test that path traversal attacks are blocked"""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            temp_safe_dir + "/../../../etc/passwd", 
            temp_safe_dir + "/../../etc/passwd",
            os.path.join(temp_safe_dir, "..", "..", "etc", "passwd"),
            "test.md/../../../etc/passwd",
            "/etc/passwd",
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
            "~/../../etc/passwd",
            "%SYSTEMROOT%\\system32\\config\\sam"
        ]
        
        for dangerous_path in dangerous_paths:
            with pytest.raises(SecurityError, match="Forbidden path component|Forbidden character|Suspicious path|not within allowed"):
                SecureFileHandler.validate_file_path(dangerous_path, {temp_safe_dir})

    def test_null_byte_injection_blocked(self):
        """Test that null byte injection is blocked"""
        dangerous_paths = [
            "test.md\x00.txt",
            "test\x00/../../etc/passwd",
            "/safe/file.md\x00/../../etc/passwd"
        ]
        
        for dangerous_path in dangerous_paths:
            with pytest.raises(SecurityError):
                SecureFileHandler.validate_file_path(dangerous_path)

    def test_control_character_injection_blocked(self):
        """Test that control characters are blocked"""
        dangerous_paths = [
            "test\n.md",
            "test\r.md", 
            "test\t.md",
            "test\x0b.md"  # vertical tab
        ]
        
        for dangerous_path in dangerous_paths:
            with pytest.raises(SecurityError):
                SecureFileHandler.validate_file_path(dangerous_path)

    def test_forbidden_extensions_blocked(self, temp_safe_dir):
        """Test that dangerous file extensions are blocked"""
        dangerous_extensions = [
            "test.exe",
            "test.bat", 
            "test.sh",
            "test.py",
            "test.php",
            "test.js",
            "test.html",
            "test.xml"
        ]
        
        for dangerous_file in dangerous_extensions:
            file_path = os.path.join(temp_safe_dir, dangerous_file)
            # Create the file
            with open(file_path, 'w') as f:
                f.write("content")
            
            with pytest.raises(SecurityError, match="File extension.*not allowed"):
                SecureFileHandler.validate_file_extension(file_path)

    def test_allowed_extensions_accepted(self, temp_safe_dir):
        """Test that safe extensions are allowed"""
        safe_extensions = [".md", ".txt", ".json", ".csv"]
        
        for ext in safe_extensions:
            test_file = os.path.join(temp_safe_dir, f"test{ext}")
            with open(test_file, 'w') as f:
                f.write("safe content")
            
            # Should not raise exception
            SecureFileHandler.validate_file_extension(test_file)

    def test_file_size_limits_enforced(self, temp_safe_dir):
        """Test that file size limits are enforced"""
        large_file = os.path.join(temp_safe_dir, "large.md")
        
        # Create file larger than limit (11MB > 10MB limit)
        with open(large_file, 'w') as f:
            # Write 11MB of data
            chunk_size = 1024 * 1024  # 1MB chunks
            for _ in range(11):
                f.write('x' * chunk_size)
        
        with pytest.raises(SecurityError, match="File too large"):
            SecureFileHandler.validate_file_size(large_file)

    def test_directory_traversal_via_symlinks_blocked(self, temp_safe_dir):
        """Test that symlink-based directory traversal is blocked"""
        if os.name == 'nt':  # Skip on Windows (symlink restrictions)
            pytest.skip("Symlink test skipped on Windows")
        
        # Create symlink pointing outside safe directory
        symlink_path = os.path.join(temp_safe_dir, "evil_symlink")
        
        try:
            os.symlink("/etc/passwd", symlink_path)
            
            with pytest.raises(SecurityError):
                SecureFileHandler.validate_file_path(symlink_path, {temp_safe_dir})
        except OSError:
            # Permission denied creating symlink - skip test
            pytest.skip("Cannot create symlink for testing")

    def test_secure_file_read_integration(self, temp_safe_dir):
        """Test complete secure file reading"""
        test_file = os.path.join(temp_safe_dir, "safe.md")
        test_content = "# Safe Content\n- Item 1\n- Item 2"
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Should successfully read safe file
        content = SecureFileHandler.secure_file_read(test_file, {temp_safe_dir})
        assert content == test_content

    def test_secure_file_read_blocks_dangerous_paths(self, temp_safe_dir):
        """Test that secure_file_read blocks dangerous paths"""
        dangerous_paths = [
            "../../../etc/passwd",
            "/etc/passwd", 
            os.path.join(temp_safe_dir, "..", "dangerous.md")
        ]
        
        for dangerous_path in dangerous_paths:
            with pytest.raises(SecurityError):
                SecureFileHandler.secure_file_read(dangerous_path, {temp_safe_dir})

    def test_nonexistent_file_handling(self, temp_safe_dir):
        """Test handling of nonexistent files"""
        nonexistent = os.path.join(temp_safe_dir, "nonexistent.md")
        
        with pytest.raises(SecurityError, match="File does not exist"):
            SecureFileHandler.secure_file_read(nonexistent, {temp_safe_dir})

    def test_directory_instead_of_file_blocked(self, temp_safe_dir):
        """Test that directories are rejected when expecting files"""
        # temp_safe_dir is a directory, not a file
        with pytest.raises(SecurityError, match="not a regular file"):
            SecureFileHandler.secure_file_read(temp_safe_dir, {temp_safe_dir})

    def test_empty_and_invalid_paths_blocked(self):
        """Test that empty and invalid paths are blocked"""
        invalid_paths = [
            "",
            None,
            "\x00",
            "   ",
            "\t\n\r"
        ]
        
        for invalid_path in invalid_paths:
            with pytest.raises(SecurityError):
                if invalid_path is None:
                    SecureFileHandler.validate_file_path(invalid_path)
                else:
                    SecureFileHandler.validate_file_path(invalid_path)