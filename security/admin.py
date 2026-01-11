"""
Admin configuration for Security models.
"""

from django.contrib import admin
from .models import ApiChallengeToken, ApiNonce


@admin.register(ApiChallengeToken)
class ApiChallengeTokenAdmin(admin.ModelAdmin):
    """Admin interface for API Challenge Tokens."""
    list_display = ['token_short', 'created_at', 'expires_at', 'is_expired', 'is_revoked', 'ip_address']
    list_filter = ['is_revoked', 'created_at', 'expires_at']
    search_fields = ['token', 'ip_address']
    readonly_fields = ['id', 'token', 'secret', 'created_at', 'expires_at']
    ordering = ['-created_at']
    
    def token_short(self, obj):
        """Display shortened token."""
        return f"{obj.token[:16]}..." if len(obj.token) > 16 else obj.token
    token_short.short_description = 'Token'
    
    def has_add_permission(self, request):
        """Disable manual token creation (use API endpoint)."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Only allow revoking tokens."""
        return True
    
    actions = ['revoke_tokens']
    
    def revoke_tokens(self, request, queryset):
        """Revoke selected tokens."""
        count = 0
        for token in queryset:
            if not token.is_revoked:
                token.revoke()
                count += 1
        self.message_user(request, f'{count} token(s) revoked.')
    revoke_tokens.short_description = 'Revoke selected tokens'


@admin.register(ApiNonce)
class ApiNonceAdmin(admin.ModelAdmin):
    """Admin interface for API Nonces."""
    list_display = ['nonce_short', 'token_short', 'used_at', 'expires_at', 'is_expired']
    list_filter = ['used_at', 'expires_at']
    search_fields = ['nonce', 'token__token']
    readonly_fields = ['nonce', 'token', 'used_at', 'expires_at']
    ordering = ['-used_at']
    
    def nonce_short(self, obj):
        """Display shortened nonce."""
        return f"{obj.nonce[:16]}..." if len(obj.nonce) > 16 else obj.nonce
    nonce_short.short_description = 'Nonce'
    
    def token_short(self, obj):
        """Display shortened token."""
        return f"{obj.token.token[:16]}..." if len(obj.token.token) > 16 else obj.token.token
    token_short.short_description = 'Token'
    
    def has_add_permission(self, request):
        """Disable manual nonce creation."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Nonces are read-only."""
        return False
