"""
Middleware for validating signed API requests.
"""

import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .services import (
    ChallengeTokenService,
    RequestSigningService,
    OriginValidator,
    SecurityError,
    TokenExpiredError,
    InvalidSignatureError,
    NonceReusedError,
    InvalidTimestampError,
)

logger = logging.getLogger(__name__)


class DisableCSRFForAPI(MiddlewareMixin):
    """
    Middleware to disable CSRF protection for API requests.
    API requests are protected by our custom request signing mechanism.
    """
    
    def process_request(self, request):
        """Disable CSRF for API endpoints."""
        # Only disable CSRF for API paths
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None


class ApiSecurityMiddleware(MiddlewareMixin):
    """
    Middleware to validate signed API requests.
    
    Excludes:
    - /api/security/challenge/ (endpoint to get tokens)
    - /admin/ (Django admin)
    - /health/ (health check)
    - /api/ (API root, just info)
    """
    
    # Paths that don't require security validation
    EXCLUDED_PATHS = [
        '/api/security/challenge/',
        '/admin/',
        '/health/',
        '/api/',  # API root endpoint
    ]
    
    # Paths that start with these prefixes are excluded
    EXCLUDED_PREFIXES = [
        '/admin/',
        '/static/',
        '/media/',
    ]
    
    def process_request(self, request):
        """
        Validate request before it reaches the view.
        """
        # Skip validation for excluded paths
        if self._should_skip_validation(request.path):
            return None
        
        # Skip OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return None
        
        # Only validate API paths
        if not request.path.startswith('/api/'):
            return None
        
        # Skip webhook endpoints (they have their own security)
        if '/webhook/' in request.path:
            return None
        
        try:
            # Validate origin
            OriginValidator.validate_origin(request)
            
            # Extract security headers
            token = request.META.get('HTTP_X_API_CHALLENGE_TOKEN')
            timestamp = request.META.get('HTTP_X_API_TIMESTAMP')
            nonce = request.META.get('HTTP_X_API_NONCE')
            signature = request.META.get('HTTP_X_API_SIGNATURE')
            
            # Check all headers are present
            if not all([token, timestamp, nonce, signature]):
                logger.warning(f"Missing security headers for {request.path}")
                return JsonResponse(
                    {'error': 'Missing required security headers'},
                    status=401
                )
            
            # Validate token
            try:
                token_obj = ChallengeTokenService.validate_token(token)
            except TokenExpiredError as e:
                logger.warning(f"Token validation failed: {e}")
                return JsonResponse(
                    {'error': 'Invalid or expired token'},
                    status=401
                )
            
            # Validate timestamp
            try:
                RequestSigningService.validate_timestamp(timestamp)
            except InvalidTimestampError as e:
                logger.warning(f"Timestamp validation failed: {e}")
                return JsonResponse(
                    {'error': str(e)},
                    status=401
                )
            
            # Check nonce hasn't been used
            try:
                RequestSigningService.check_nonce(token_obj, nonce)
            except NonceReusedError as e:
                logger.warning(f"Nonce validation failed: {e}")
                return JsonResponse(
                    {'error': 'Nonce has already been used'},
                    status=401
                )
            
            # Calculate body hash
            body_hash = RequestSigningService.hash_body(request.body)
            
            # Extract method and path
            method = request.method
            path = request.path
            
            # Validate signature
            try:
                RequestSigningService.validate_signature(
                    token=token,
                    timestamp=timestamp,
                    nonce=nonce,
                    method=method,
                    path=path,
                    body_hash=body_hash,
                    signature=signature
                )
            except InvalidSignatureError as e:
                logger.warning(f"Signature validation failed: {e}")
                return JsonResponse(
                    {'error': 'Invalid signature'},
                    status=401
                )
            
            # All validations passed
            logger.debug(f"Request validated successfully: {method} {path}")
            return None
            
        except SecurityError as e:
            logger.warning(f"Security validation failed: {e}")
            return JsonResponse(
                {'error': str(e)},
                status=401
            )
        except Exception as e:
            logger.error(f"Unexpected error in security middleware: {e}", exc_info=True)
            # In production, don't expose internal errors
            if getattr(settings, 'DEBUG', False):
                return JsonResponse(
                    {'error': f'Security validation error: {str(e)}'},
                    status=500
                )
            return JsonResponse(
                {'error': 'Security validation failed'},
                status=500
            )
    
    def _should_skip_validation(self, path):
        """Check if path should skip validation."""
        # Check exact matches
        if path in self.EXCLUDED_PATHS:
            return True
        
        # Check prefixes
        for prefix in self.EXCLUDED_PREFIXES:
            if path.startswith(prefix):
                return True
        
        return False
