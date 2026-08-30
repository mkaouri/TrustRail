class DomainError(Exception):
    """Base class for domain/service errors mapped to clean HTTP responses."""


class OrganizationNotFoundError(DomainError):
    """The requested organization does not exist."""


class OrganizationSlugConflictError(DomainError):
    """An organization with the requested slug already exists."""
