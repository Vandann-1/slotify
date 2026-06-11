import contextvars
from typing import Optional

# Define a context variable to store the current active tenant
_current_tenant = contextvars.ContextVar("current_tenant", default=None)


def set_current_tenant(tenant) -> contextvars.Token:
    """
    Set the current tenant in the thread-safe context.
    Returns a Token that can be used to reset the context later.
    """
    return _current_tenant.set(tenant)


def get_current_tenant():
    """
    Retrieve the current tenant from the thread-safe context.
    Returns None if no tenant is active in the current context.
    """
    return _current_tenant.get()


def clear_current_tenant(token: Optional[contextvars.Token] = None):
    """
    Reset or clear the current tenant context.
    """
    if token is not None:
        _current_tenant.reset(token)
    else:
        _current_tenant.set(None)
