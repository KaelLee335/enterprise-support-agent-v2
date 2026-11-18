"""Safe, provider-neutral failures exposed by platform adapters."""


class IntegrationError(RuntimeError):
    code = "platform_error"
    retryable = False


class IntegrationNotFound(IntegrationError):
    code = "not_found"


class IntegrationUnauthorized(IntegrationError):
    code = "platform_auth_failed"


class IntegrationConflict(IntegrationError):
    code = "conflict"


class IntegrationRejected(IntegrationError):
    code = "request_rejected"


class IntegrationUnavailable(IntegrationError):
    code = "platform_unavailable"
    retryable = True


class IntegrationInvalidResponse(IntegrationError):
    code = "invalid_platform_response"


class IntegrationProtocolError(IntegrationError):
    code = "unsupported_platform_value"
