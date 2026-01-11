"""
Security models for API challenge tokens and nonce tracking.
"""

import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


class ApiChallengeToken(models.Model):
    """
    Challenge token issued to frontend for request signing.
    Tokens expire after a configured time period.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=64, unique=True, db_index=True)
    secret = models.CharField(max_length=64)  # Secret used for HMAC signing
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    is_revoked = models.BooleanField(default=False)
    
    # Optional: track IP address for additional security
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'API Challenge Token'
        verbose_name_plural = 'API Challenge Tokens'
        indexes = [
            models.Index(fields=['token', 'expires_at']),
        ]
    
    def __str__(self):
        return f"Token {self.token[:8]}... (expires: {self.expires_at})"
    
    @property
    def is_expired(self):
        """Check if token has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid (not expired and not revoked)."""
        return not self.is_expired and not self.is_revoked
    
    def revoke(self):
        """Revoke this token."""
        self.is_revoked = True
        self.save(update_fields=['is_revoked'])


class ApiNonce(models.Model):
    """
    Track used nonces to prevent replay attacks.
    Nonces are stored temporarily and cleaned up after expiry.
    """
    nonce = models.CharField(max_length=64, unique=True, db_index=True)
    token = models.ForeignKey(
        ApiChallengeToken,
        on_delete=models.CASCADE,
        related_name='nonces'
    )
    used_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    
    class Meta:
        ordering = ['-used_at']
        verbose_name = 'API Nonce'
        verbose_name_plural = 'API Nonces'
        indexes = [
            models.Index(fields=['nonce', 'expires_at']),
            models.Index(fields=['token', 'expires_at']),
        ]
    
    def __str__(self):
        return f"Nonce {self.nonce[:8]}... (used: {self.used_at})"
    
    @property
    def is_expired(self):
        """Check if nonce has expired."""
        return timezone.now() > self.expires_at
