
def check_permission(user, permission_name: str) -> bool:
    """Implement a basic permission check.
    For this version, we require OWNER role for high-level permissions,
    or explicit user-granted permissions if it was a real ACL system.
    """
    from accounts.models import User

    # Example logic: Owners get ai.* and memory.*
    # We will expand this as needed.
    if user.role == User.OWNER:
        return True

    # Restrict destructive operations for viewers
    if "write" in permission_name:
        return False

    return True

def has_integration(user, integration_name: str) -> bool:
    """Return True if user has configured the third-party integration."""
    # This will tie into Phase 3's IntegrationConnection model
    # For now, we mock it explicitly or check if it's GitHub
    if integration_name == "github":
        return bool(user.github_username)
    return False

def check_provider_capabilities(conn, required: list) -> bool:
    """Check if the chosen provider connection has the required capabilities."""
    if not required:
        return True

    for cap in required:
        if cap == "streaming" and not conn.provider.supports_streaming:
            return False
        if cap == "tools" and not conn.provider.supports_tools:
            return False
        if cap == "embeddings" and not conn.provider.supports_embeddings:
            return False

    return True
