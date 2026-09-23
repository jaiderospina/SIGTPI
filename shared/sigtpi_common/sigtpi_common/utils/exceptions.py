from fastapi import HTTPException, status

class SIGTPIException(Exception):
    def __init__(self, message: str, code: str = "SIGTPI_ERROR"):
        self.message = message; self.code = code; super().__init__(message)

class NotFoundError(SIGTPIException):
    def __init__(self, resource: str, identifier):
        super().__init__(f"{resource} '{identifier}' not found.", code="NOT_FOUND")

class UnauthorizedError(SIGTPIException):
    def __init__(self, detail: str = "Authentication required."):
        super().__init__(detail, code="UNAUTHORIZED")

class ForbiddenError(SIGTPIException):
    def __init__(self, detail: str = "Permission denied."):
        super().__init__(detail, code="FORBIDDEN")

class ConflictError(SIGTPIException):
    def __init__(self, detail: str):
        super().__init__(detail, code="CONFLICT")

def http_not_found(resource: str, identifier) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} '{identifier}' not found.")

def http_unauthorized(detail: str = "Authentication required.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"})

def http_forbidden(detail: str = "Permission denied.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
