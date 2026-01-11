"""
Security services for API challenge tokens and request signing.
"""

import hashlib
import hmac
import secrets
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache

from .models import ApiChallengeToken, ApiNonce

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Base exception for security-related errors."""
    pass


class TokenExpiredError(SecurityError):
    """Token has expired."""
    pass


class InvalidSignatureError(SecurityError):
    """Request signature is invalid."""
    pass


class NonceReusedError(SecurityError):
    """Nonce has already been used."""
    pass


class InvalidTimestampError(SecurityError):
    """Request timestamp is outside tolerance window."""
    pass


class ChallengeTokenService:
    """Service for generating and validating challenge tokens."""
    
    @staticmethod
    def generate_token(ip_address=None):
        """
        Generate a new challenge token.
        
        Returns:
            tuple: (token_string, ApiChallengeToken instance)
        """
        # Generate random token and secret
        token = secrets.token_urlsafe(32)
        secret = secrets.token_urlsafe(32)
        
        # Calculate expiry time
        expiry_seconds = getattr(settings, 'API_CHALLENGE_TOKEN_EXPIRY', 300)  # 5 minutes default
        expires_at = timezone.now() + timedelta(seconds=expiry_seconds)
        
        # Create token record
        token_obj = ApiChallengeToken.objects.create(
            token=token,
            secret=secret,
            expires_at=expires_at,
            ip_address=ip_address,
        )
        
        logger.info(f"Generated challenge token: {token[:8]}... (expires: {expires_at})")
        return token, token_obj
    
    @staticmethod
    def validate_token(token_string):
        """
        Validate a challenge token.
        
        Returns:
            ApiChallengeToken: The token instance if valid
            
        Raises:
            TokenExpiredError: If token is expired or revoked
        """
        try:
            token_obj = ApiChallengeToken.objects.get(token=token_string)
        except ApiChallengeToken.DoesNotExist:
            logger.warning(f"Invalid token: {token_string[:8]}...")
            raise TokenExpiredError("Invalid token")
        
        if not token_obj.is_valid:
            logger.warning(f"Token expired or revoked: {token_string[:8]}...")
            raise TokenExpiredError("Token expired or revoked")
        
        return token_obj
    
    @staticmethod
    def get_token_secret(token_string):
        """
        Get the secret for a token (for signature validation).
        
        Returns:
            str: The secret string
        """
        token_obj = ChallengeTokenService.validate_token(token_string)
        return token_obj.secret


class RequestSigningService:
    """Service for signing and validating API requests."""
    
    @staticmethod
    def calculate_signature(token, secret, timestamp, nonce, method, path, body_hash=''):
        """
        Calculate HMAC signature for a request.
        
        Args:
            token: Challenge token
            secret: Secret associated with the token
            timestamp: Unix timestamp
            nonce: Unique nonce string
            method: HTTP method (GET, POST, etc.)
            path: Request path
            body_hash: SHA256 hash of request body (empty string if no body)
            
        Returns:
            str: Hex-encoded HMAC signature
        """
        # Build signature string: token|timestamp|nonce|method|path|body_hash
        signature_string = f"{token}|{timestamp}|{nonce}|{method}|{path}|{body_hash}"
        
        # Calculate HMAC-SHA256
        signature = hmac.new(
            secret.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    @staticmethod
    def validate_signature(token, timestamp, nonce, method, path, body_hash, signature):
        """
        Validate a request signature.
        
        Args:
            token: Challenge token
            timestamp: Unix timestamp
            nonce: Nonce string
            method: HTTP method
            path: Request path
            body_hash: Body hash
            signature: Provided signature
            
        Returns:
            bool: True if signature is valid
            
        Raises:
            InvalidSignatureError: If signature doesn't match
        """
        # Get token secret
        try:
            secret = ChallengeTokenService.get_token_secret(token)
        except TokenExpiredError:
            raise InvalidSignatureError("Invalid or expired token")
        
        # Calculate expected signature
        expected_signature = RequestSigningService.calculate_signature(
            token=token,
            secret=secret,
            timestamp=timestamp,
            nonce=nonce,
            method=method,
            path=path,
            body_hash=body_hash
        )
        
        # Use constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(expected_signature, signature):
            logger.warning(f"Invalid signature for token: {token[:8]}...")
            raise InvalidSignatureError("Invalid signature")
        
        return True
    
    @staticmethod
    def validate_timestamp(timestamp_str):
        """
        Validate that timestamp is within tolerance window.
        
        Args:
            timestamp_str: Unix timestamp as string
            
        Returns:
            int: Parsed timestamp
            
        Raises:
            InvalidTimestampError: If timestamp is outside tolerance
        """
        try:
            timestamp = int(timestamp_str)
        except (ValueError, TypeError):
            raise InvalidTimestampError("Invalid timestamp format")
        
        current_time = int(timezone.now().timestamp())
        tolerance = getattr(settings, 'API_REQUEST_TIMESTAMP_TOLERANCE', 60)  # 60 seconds default
        
        time_diff = abs(current_time - timestamp)
        if time_diff > tolerance:
            logger.warning(f"Timestamp outside tolerance: diff={time_diff}s, tolerance={tolerance}s")
            raise InvalidTimestampError(f"Timestamp outside tolerance window (±{tolerance}s)")
        
        return timestamp
    
    @staticmethod
    def check_nonce(token_obj, nonce):
        """
        Check if nonce has been used before.
        
        Args:
            token_obj: ApiChallengeToken instance
            nonce: Nonce string
            
        Returns:
            ApiNonce: The nonce record
            
        Raises:
            NonceReusedError: If nonce has already been used
        """
        # Check cache first (faster)
        cache_key = f"api_nonce:{nonce}"
        if cache.get(cache_key):
            logger.warning(f"Nonce reused: {nonce[:8]}...")
            raise NonceReusedError("Nonce has already been used")
        
        # Check database
        if ApiNonce.objects.filter(nonce=nonce).exists():
            logger.warning(f"Nonce reused (from DB): {nonce[:8]}...")
            raise NonceReusedError("Nonce has already been used")
        
        # Calculate expiry for nonce (same as token expiry or 5 minutes, whichever is longer)
        nonce_expiry_seconds = max(
            getattr(settings, 'API_CHALLENGE_TOKEN_EXPIRY', 300),
            300  # Minimum 5 minutes
        )
        expires_at = timezone.now() + timedelta(seconds=nonce_expiry_seconds)
        
        # Store nonce
        nonce_obj = ApiNonce.objects.create(
            nonce=nonce,
            token=token_obj,
            expires_at=expires_at
        )
        
        # Cache nonce
        cache.set(cache_key, True, timeout=nonce_expiry_seconds)
        
        return nonce_obj
    
    @staticmethod
    def hash_body(body_bytes):
        """
        Calculate SHA256 hash of request body.
        
        Args:
            body_bytes: Request body as bytes
            
        Returns:
            str: Hex-encoded hash (empty string if no body)
        """
        if not body_bytes:
            return ''
        return hashlib.sha256(body_bytes).hexdigest()


class OriginValidator:
    """Service for validating request origin."""
    
    @staticmethod
    def validate_origin(request):
        """
        Validate that request comes from allowed origin.
        
        Args:
            request: Django request object
            
        Returns:
            bool: True if origin is valid
            
        Raises:
            SecurityError: If origin is not allowed
        """
        # Get origin from headers
        origin = request.META.get('HTTP_ORIGIN') or request.META.get('HTTP_REFERER', '')
        
        # Remove path from referer if present
        if origin.startswith('http'):
            from urllib.parse import urlparse
            parsed = urlparse(origin)
            origin = f"{parsed.scheme}://{parsed.netloc}"
        
        # Get allowed frontend URL
        frontend_url = getattr(settings, 'FRONTEND_URL', '')
        if not frontend_url:
            # Fallback: allow localhost in development
            if getattr(settings, 'DEBUG', False):
                logger.warning("FRONTEND_URL not configured, allowing all origins in DEBUG mode")
                return True
            raise SecurityError("FRONTEND_URL not configured")
        
        # Normalize URLs (remove trailing slashes)
        origin = origin.rstrip('/')
        frontend_url = frontend_url.rstrip('/')
        
        # Check if origin matches
        if origin != frontend_url:
            # In development, also allow localhost variants
            if getattr(settings, 'DEBUG', False):
                localhost_variants = [
                    'http://localhost:3000',
                    'http://127.0.0.1:3000',
                    'http://localhost:5173',  # Vite default
                    'http://127.0.0.1:5173',
                ]
                if origin in localhost_variants:
                    return True
            
            logger.warning(f"Invalid origin: {origin} (expected: {frontend_url})")
            raise SecurityError(f"Invalid origin: {origin}")
        
        return True
