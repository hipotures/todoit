"""
Security utilities for TODOIT MCP
Provides secure file handling and path validation
"""

import os
import re
from pathlib import Path
from typing import Optional, Set


class SecurityError(Exception):
    """Raised when security validation fails"""
    pass


class SecureFileHandler:
    """Secure file operations with path traversal protection"""
    
    # Allowed file extensions for import/export
    ALLOWED_EXTENSIONS: Set[str] = {'.md', '.txt', '.json', '.csv'}
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    
    # Forbidden path components (dangerous path elements)
    FORBIDDEN_COMPONENTS: Set[str] = {
        '..', '~', '$', '%', '*', '?', '<', '>', '|', '"', "'",
        '\x00', '\n', '\r', '\t', '\x0b', '\x0c', '\x0d', '\x0e', '\x0f'
    }
    
    @staticmethod
    def validate_file_path(file_path: str, allowed_base_dirs: Optional[Set[str]] = None) -> str:
        """
        Validate and sanitize file path to prevent path traversal attacks
        
        Args:
            file_path: Path to validate
            allowed_base_dirs: Set of allowed base directories (optional)
            
        Returns:
            Resolved absolute path if valid
            
        Raises:
            SecurityError: If path is malicious or invalid
        """
        if not file_path or not isinstance(file_path, str):
            raise SecurityError("File path must be a non-empty string")
        
        # Remove any null bytes and control characters early
        cleaned_path = file_path.replace('\x00', '').strip()
        if not cleaned_path:
            raise SecurityError("File path cannot be empty after sanitization")
        
        # Check for any remaining null bytes or control characters in original
        for forbidden in ['\x00', '\n', '\r', '\t', '\x0b', '\x0c', '\x0d', '\x0e', '\x0f']:
            if forbidden in file_path:
                raise SecurityError(f"Forbidden character detected in path: {repr(forbidden)}")
        
        try:
            # Convert to Path object for normalization
            path_obj = Path(cleaned_path)
            
            # Check for forbidden components in any part of the path
            for part in path_obj.parts:
                # Check for exact matches
                if part in SecureFileHandler.FORBIDDEN_COMPONENTS:
                    raise SecurityError(f"Forbidden path component detected: {part}")
                
                # Check for forbidden characters within the part
                for forbidden in SecureFileHandler.FORBIDDEN_COMPONENTS:
                    if forbidden in part:
                        raise SecurityError(f"Forbidden character '{forbidden}' in path component: {part}")
                
                # Check for suspicious patterns (only double dots, not single dots)
                if '..' in part:
                    raise SecurityError(f"Suspicious path component: {part}")
            
            # Resolve to absolute path (this also resolves symlinks)
            resolved_path = path_obj.resolve()
            
            # If allowed base directories are specified, enforce them
            if allowed_base_dirs:
                path_str = str(resolved_path)
                if not any(path_str.startswith(base_dir) for base_dir in allowed_base_dirs):
                    raise SecurityError(f"Path not within allowed directories: {path_str}")
            
            return str(resolved_path)
            
        except (OSError, ValueError) as e:
            raise SecurityError(f"Invalid file path: {e}")
    
    @staticmethod
    def validate_file_extension(file_path: str) -> None:
        """
        Validate file extension against allowed list
        
        Args:
            file_path: Path to check
            
        Raises:
            SecurityError: If extension is not allowed
        """
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()
        
        if extension not in SecureFileHandler.ALLOWED_EXTENSIONS:
            allowed = ', '.join(SecureFileHandler.ALLOWED_EXTENSIONS)
            raise SecurityError(f"File extension '{extension}' not allowed. Allowed: {allowed}")
    
    @staticmethod
    def validate_file_size(file_path: str) -> None:
        """
        Validate file size against maximum limit
        
        Args:
            file_path: Path to check
            
        Raises:
            SecurityError: If file is too large
        """
        try:
            file_size = os.path.getsize(file_path)
            if file_size > SecureFileHandler.MAX_FILE_SIZE:
                max_mb = SecureFileHandler.MAX_FILE_SIZE // (1024 * 1024)
                current_mb = file_size // (1024 * 1024)
                raise SecurityError(f"File too large: {current_mb}MB (max: {max_mb}MB)")
        except OSError as e:
            raise SecurityError(f"Cannot check file size: {e}")
    
    @staticmethod
    def secure_file_read(file_path: str, allowed_base_dirs: Optional[Set[str]] = None) -> str:
        """
        Securely read file content with full validation
        
        Args:
            file_path: Path to read
            allowed_base_dirs: Set of allowed base directories
            
        Returns:
            File content as string
            
        Raises:
            SecurityError: If any security validation fails
        """
        # Validate and sanitize path
        safe_path = SecureFileHandler.validate_file_path(file_path, allowed_base_dirs)
        
        # Check if file exists
        if not os.path.exists(safe_path):
            raise SecurityError(f"File does not exist: {safe_path}")
        
        # Ensure it's a regular file (not directory, device, etc.)
        if not os.path.isfile(safe_path):
            raise SecurityError(f"Path is not a regular file: {safe_path}")
        
        # Validate extension (after we know it's a file)
        SecureFileHandler.validate_file_extension(safe_path)
        
        # Validate file size
        SecureFileHandler.validate_file_size(safe_path)
        
        try:
            # Read file content with explicit encoding
            with open(safe_path, 'r', encoding='utf-8', errors='strict') as f:
                return f.read()
        except (OSError, UnicodeDecodeError) as e:
            raise SecurityError(f"Cannot read file: {e}")
    
    @staticmethod
    def get_safe_work_directory() -> str:
        """
        Get a safe working directory for file operations
        
        Returns:
            Path to safe working directory
        """
        # Use user's home directory or temp directory as safe base
        home_dir = os.path.expanduser("~")
        if os.path.exists(home_dir) and os.access(home_dir, os.R_OK | os.W_OK):
            safe_dir = os.path.join(home_dir, "todoit_imports")
        else:
            import tempfile
            safe_dir = os.path.join(tempfile.gettempdir(), "todoit_imports")
        
        # Create directory if it doesn't exist
        os.makedirs(safe_dir, mode=0o700, exist_ok=True)
        return safe_dir
    
    @staticmethod
    def secure_file_write(file_path: str, content: str, allowed_base_dirs: Optional[Set[str]] = None) -> None:
        """
        Securely write content to file with full validation
        
        Args:
            file_path: Path to write to
            content: Content to write
            allowed_base_dirs: Set of allowed base directories
            
        Raises:
            SecurityError: If any security validation fails
        """
        # Validate and sanitize path
        safe_path = SecureFileHandler.validate_file_path(file_path, allowed_base_dirs)
        
        # Validate extension
        SecureFileHandler.validate_file_extension(safe_path)
        
        # Ensure parent directory exists and is safe
        parent_dir = os.path.dirname(safe_path)
        if not os.path.exists(parent_dir):
            try:
                # Create parent directories with secure permissions
                os.makedirs(parent_dir, mode=0o700, exist_ok=True)
            except OSError as e:
                raise SecurityError(f"Cannot create directory: {e}")
        
        # Validate content size
        content_size = len(content.encode('utf-8'))
        if content_size > SecureFileHandler.MAX_FILE_SIZE:
            max_mb = SecureFileHandler.MAX_FILE_SIZE // (1024 * 1024)
            current_mb = content_size // (1024 * 1024)
            raise SecurityError(f"Content too large: {current_mb}MB (max: {max_mb}MB)")
        
        try:
            # Write file content with explicit encoding and secure permissions
            with open(safe_path, 'w', encoding='utf-8', errors='strict') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk
            
            # Set secure file permissions (readable/writable by owner only)
            os.chmod(safe_path, 0o600)
            
        except (OSError, UnicodeEncodeError) as e:
            raise SecurityError(f"Cannot write file: {e}")