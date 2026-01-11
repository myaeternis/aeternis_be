"""
API Views for Security endpoints.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from .services import ChallengeTokenService, OriginValidator, SecurityError

logger = logging.getLogger(__name__)


class ChallengeView(APIView):
    """
    POST /api/security/challenge/
    
    Request a challenge token for API request signing.
    This endpoint does NOT require authentication (it's the entry point).
    
    Returns:
    {
        "token": "challenge_token_string",
        "expires_at": "2024-01-01T12:00:00Z",
        "expires_in": 300
    }
    """
    
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        """
        Generate a new challenge token.
        """
        try:
            # Validate origin (but don't fail in development)
            try:
                OriginValidator.validate_origin(request)
            except SecurityError as e:
                # In development, log but don't fail
                if getattr(settings, 'DEBUG', False):
                    logger.warning(f"Origin validation failed in DEBUG mode: {e}")
                else:
                    return Response(
                        {'error': str(e)},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Get client IP
            ip_address = self._get_client_ip(request)
            
            # Generate token
            token_string, token_obj = ChallengeTokenService.generate_token(
                ip_address=ip_address
            )
            
            # Calculate expiry info
            from django.utils import timezone
            expires_in = int((token_obj.expires_at - timezone.now()).total_seconds())
            
            logger.info(f"Challenge token issued: {token_string[:8]}... (IP: {ip_address})")
            
            # Return token and secret (secret is needed for client-side signing)
            # Security is maintained through:
            # - Token expiry (5 minutes)
            # - Nonce tracking (prevents replay)
            # - Timestamp validation (prevents old requests)
            # - Origin validation
            return Response({
                'token': token_string,
                'secret': token_obj.secret,  # Secret for signing requests
                'expires_at': token_obj.expires_at.isoformat(),
                'expires_in': expires_in,
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error generating challenge token: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to generate challenge token'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
