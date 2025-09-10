"""
LocalMind Security Manager

Handles privacy protection, data encryption, and content filtering
for secure LIVE-OFFLINE operation.
"""

import logging
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("Cryptography not available - using basic security measures")

class SecurityManager:
    """
    Security and privacy manager for LocalMind.
    
    Features:
    - Data encryption and privacy protection
    - Content filtering and safety checks
    - User data anonymization
    - Secure local storage
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Security configuration
        self.encryption_enabled = config['security']['encryption']['enabled']
        self.anonymize_logs = config['security']['privacy']['anonymize_logs']
        self.local_only = config['security']['privacy']['local_only']
        self.content_filter_enabled = config['security']['content_filter']['enabled']
        self.strict_mode = config['security']['content_filter']['strict_mode']
        
        # Encryption setup
        self.encryption_key = None
        if self.encryption_enabled and CRYPTO_AVAILABLE:
            self._setup_encryption()
        
        # Content filtering
        self.blocked_categories = config['security']['content_filter']['blocked_categories']
        self.custom_filters = config['security']['content_filter'].get('custom_filters', [])
        
        # Privacy settings
        self.data_retention_days = config['security']['privacy']['data_retention_days']
        
        # Security directories
        self.security_dir = Path("data/user/security")
        self.security_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("SecurityManager initialized")
        self.logger.info(f"Encryption: {'enabled' if self.encryption_enabled else 'disabled'}")
        self.logger.info(f"Content filtering: {'enabled' if self.content_filter_enabled else 'disabled'}")
    
    def _setup_encryption(self):
        """Setup encryption key for data protection."""
        try:
            key_file = self.security_dir / "encryption.key"
            
            if key_file.exists():
                # Load existing key
                with open(key_file, 'rb') as f:
                    self.encryption_key = f.read()
                self.logger.debug("Encryption key loaded")
            else:
                # Generate new key
                self.encryption_key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(self.encryption_key)
                # Set file permissions to read-only for owner
                os.chmod(key_file, 0o600)
                self.logger.info("New encryption key generated")
                
        except Exception as e:
            self.logger.error(f"Failed to setup encryption: {e}")
            self.encryption_enabled = False
    
    def encrypt_data(self, data: str) -> Optional[bytes]:
        """
        Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data or None if failed
        """
        if not self.encryption_enabled or not CRYPTO_AVAILABLE:
            return data.encode()  # Return as bytes without encryption
        
        try:
            fernet = Fernet(self.encryption_key)
            encrypted = fernet.encrypt(data.encode())
            return encrypted
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            return None
    
    def decrypt_data(self, encrypted_data: bytes) -> Optional[str]:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Data to decrypt
            
        Returns:
            Decrypted data or None if failed
        """
        if not self.encryption_enabled or not CRYPTO_AVAILABLE:
            try:
                return encrypted_data.decode()  # Assume it's plain text
            except:
                return None
        
        try:
            fernet = Fernet(self.encryption_key)
            decrypted = fernet.decrypt(encrypted_data)
            return decrypted.decode()
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return None
    
    def anonymize_text(self, text: str) -> str:
        """
        Anonymize text by removing or hashing personal information.
        
        Args:
            text: Text to anonymize
            
        Returns:
            Anonymized text
        """
        if not self.anonymize_logs:
            return text
        
        try:
            anonymized = text
            
            # Replace potential personal identifiers with hashes
            import re
            
            # Email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, anonymized)
            for email in emails:
                hash_val = hashlib.md5(email.encode()).hexdigest()[:8]
                anonymized = anonymized.replace(email, f"email_{hash_val}")
            
            # Phone numbers (simple pattern)
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            phones = re.findall(phone_pattern, anonymized)
            for phone in phones:
                hash_val = hashlib.md5(phone.encode()).hexdigest()[:8]
                anonymized = anonymized.replace(phone, f"phone_{hash_val}")
            
            # Credit card numbers (basic pattern)
            cc_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
            ccs = re.findall(cc_pattern, anonymized)
            for cc in ccs:
                anonymized = anonymized.replace(cc, "CARD_REDACTED")
            
            # Social security numbers (US format)
            ssn_pattern = r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'
            ssns = re.findall(ssn_pattern, anonymized)
            for ssn in ssns:
                anonymized = anonymized.replace(ssn, "SSN_REDACTED")
            
            return anonymized
            
        except Exception as e:
            self.logger.error(f"Anonymization failed: {e}")
            return text
    
    def filter_content(self, content: str, context: Optional[str] = None) -> Tuple[bool, str]:
        """
        Filter content for safety and appropriateness.
        
        Args:
            content: Content to filter
            context: Optional context for filtering
            
        Returns:
            Tuple of (is_safe, filtered_content or reason)
        """
        if not self.content_filter_enabled:
            return True, content
        
        try:
            content_lower = content.lower()
            
            # Check blocked categories
            for category in self.blocked_categories:
                if self._check_category_violation(content_lower, category):
                    return False, f"Content blocked: {category} content detected"
            
            # Check custom filters
            for filter_pattern in self.custom_filters:
                if filter_pattern.lower() in content_lower:
                    return False, f"Content blocked: custom filter triggered"
            
            # Strict mode additional checks
            if self.strict_mode:
                if self._strict_mode_check(content_lower):
                    return False, "Content blocked: strict mode filter"
            
            # Domain-specific filtering
            if context:
                safety_check = self._domain_specific_filter(content, context)
                if not safety_check[0]:
                    return safety_check
            
            return True, content
            
        except Exception as e:
            self.logger.error(f"Content filtering failed: {e}")
            return True, content  # Default to allowing content if filtering fails
    
    def _check_category_violation(self, content: str, category: str) -> bool:
        """Check if content violates a specific category."""
        category_patterns = {
            'adult': ['sex', 'porn', 'explicit', 'nude', 'adult content'],
            'violence': ['kill', 'murder', 'violence', 'weapon', 'attack', 'harm'],
            'harmful': ['suicide', 'self-harm', 'dangerous', 'illegal', 'drugs'],
            'illegal': ['illegal', 'criminal', 'fraud', 'scam', 'hack']
        }
        
        patterns = category_patterns.get(category, [])
        return any(pattern in content for pattern in patterns)
    
    def _strict_mode_check(self, content: str) -> bool:
        """Additional checks for strict mode."""
        # Strict mode patterns
        strict_patterns = [
            'password', 'credit card', 'social security', 'bank account',
            'personal information', 'private', 'confidential'
        ]
        
        return any(pattern in content for pattern in strict_patterns)
    
    def _domain_specific_filter(self, content: str, domain: str) -> Tuple[bool, str]:
        """Apply domain-specific content filtering."""
        if domain == 'healthcare':
            # Healthcare content should have disclaimers for medical advice
            medical_advice_patterns = ['diagnose', 'treatment', 'medication', 'cure']
            if any(pattern in content.lower() for pattern in medical_advice_patterns):
                disclaimer = "\n\n⚠️ DISCLAIMER: This information is for educational purposes only and should not replace professional medical advice."
                return True, content + disclaimer
        
        elif domain == 'education':
            # Education content filtering (less strict)
            inappropriate_patterns = ['cheat', 'plagiarize', 'copy homework']
            if any(pattern in content.lower() for pattern in inappropriate_patterns):
                return False, "Educational content should promote academic integrity"
        
        return True, content
    
    def validate_user_input(self, user_input: str) -> Tuple[bool, str]:
        """
        Validate and sanitize user input.
        
        Args:
            user_input: User input to validate
            
        Returns:
            Tuple of (is_valid, sanitized_input or error_message)
        """
        try:
            # Length check
            if len(user_input) > 2000:
                return False, "Input too long (maximum 2000 characters)"
            
            # Empty input check
            if not user_input.strip():
                return False, "Input cannot be empty"
            
            # Content filtering
            is_safe, result = self.filter_content(user_input)
            if not is_safe:
                return False, result
            
            # Sanitize input
            sanitized = self._sanitize_input(user_input)
            
            return True, sanitized
            
        except Exception as e:
            self.logger.error(f"Input validation failed: {e}")
            return False, "Input validation error"
    
    def _sanitize_input(self, text: str) -> str:
        """Sanitize user input to prevent issues."""
        # Remove control characters
        sanitized = ''.join(char for char in text if ord(char) >= 32 or char in ['\n', '\t'])
        
        # Limit consecutive whitespace
        import re
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        return sanitized.strip()
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """
        Log security-related events.
        
        Args:
            event_type: Type of security event
            details: Event details
        """
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'details': self.anonymize_text(str(details)) if self.anonymize_logs else details
            }
            
            log_file = self.security_dir / "security_events.jsonl"
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")
    
    def cleanup_old_data(self):
        """Clean up old data based on retention policy."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.data_retention_days)
            
            # Clean up log files
            log_files = [
                self.security_dir / "security_events.jsonl",
                Path("logs") / "localmind.log"
            ]
            
            for log_file in log_files:
                if log_file.exists():
                    self._cleanup_log_file(log_file, cutoff_date)
            
            # Clean up user data if configured
            if self.config['security']['privacy'].get('delete_on_exit', False):
                self._cleanup_user_data()
            
        except Exception as e:
            self.logger.error(f"Data cleanup failed: {e}")
    
    def _cleanup_log_file(self, log_file: Path, cutoff_date: datetime):
        """Clean up old entries from a log file."""
        try:
            if not log_file.exists():
                return
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            filtered_lines = []
            for line in lines:
                try:
                    log_entry = json.loads(line.strip())
                    entry_date = datetime.fromisoformat(log_entry['timestamp'])
                    if entry_date >= cutoff_date:
                        filtered_lines.append(line)
                except:
                    # Keep lines that can't be parsed
                    filtered_lines.append(line)
            
            with open(log_file, 'w') as f:
                f.writelines(filtered_lines)
            
            self.logger.debug(f"Cleaned up old entries from {log_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup log file {log_file}: {e}")
    
    def _cleanup_user_data(self):
        """Clean up user-specific data."""
        try:
            user_data_dir = Path("data/user")
            
            # Remove user history
            history_dir = user_data_dir / "history"
            if history_dir.exists():
                for file in history_dir.glob("*"):
                    file.unlink()
            
            # Remove learning data
            learning_dir = user_data_dir / "learning"
            if learning_dir.exists():
                for file in learning_dir.glob("*"):
                    file.unlink()
            
            self.logger.info("User data cleaned up")
            
        except Exception as e:
            self.logger.error(f"User data cleanup failed: {e}")
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status and configuration."""
        return {
            'encryption_enabled': self.encryption_enabled,
            'crypto_available': CRYPTO_AVAILABLE,
            'content_filtering': self.content_filter_enabled,
            'strict_mode': self.strict_mode,
            'anonymize_logs': self.anonymize_logs,
            'local_only': self.local_only,
            'data_retention_days': self.data_retention_days,
            'blocked_categories': self.blocked_categories
        }
    
    def verify_offline_mode(self) -> bool:
        """Verify that the system is operating in offline mode."""
        if not self.local_only:
            return True
        
        # Check for any network connections (basic check)
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('8.8.8.8', 53))
            sock.close()
            
            if result == 0:
                self.log_security_event('network_detected', 
                    {'message': 'Internet connection detected in offline mode'})
                return False
            
            return True
            
        except Exception:
            # If we can't check, assume offline
            return True
