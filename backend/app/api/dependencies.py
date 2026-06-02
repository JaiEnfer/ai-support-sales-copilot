"""Reusable FastAPI dependencies for auth, tracing, and tenant context."""

from secrets import compare_digest
from uuid import uuid4

from fastapi import Header, HTTPException, Request, status

from backend.app.core.config import settings
from backend.app.services.company_admin_auth import verify_company_admin_token

REQUEST_ID_HEADER = "X-Request-ID"
API_KEY_HEADER = "X-API-Key"
COMPANY_ID_HEADER = "X-Company-ID"
AUTHORIZATION_HEADER = "Authorization"


def get_request_id(request: Request) -> str:
    """Read the request ID assigned by middleware."""
    return getattr(request.state, "request_id", "")


def require_admin_api_key(x_api_key: str | None = Header(default=None, alias=API_KEY_HEADER)) -> None:
    """Protect admin/document routes when an admin key is configured."""
    expected_api_key = settings.admin_api_key
    if not expected_api_key:
        return
    if x_api_key and compare_digest(x_api_key, expected_api_key):
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key.",
    )


def require_chat_api_key(x_api_key: str | None = Header(default=None, alias=API_KEY_HEADER)) -> None:
    """Protect chat routes when a shared chat key is configured."""
    expected_api_key = settings.chat_api_key
    if not expected_api_key:
        return
    if x_api_key and compare_digest(x_api_key, expected_api_key):
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key.",
    )


def resolve_company_id(
    request: Request,
    x_company_id: str | None = Header(default=None, alias=COMPANY_ID_HEADER),
) -> str:
    """Resolve tenant context from headers first, then configured defaults."""
    company_id = x_company_id or getattr(request.state, "company_id", None) or settings.default_company_id
    if settings.require_company_id and not company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company ID is required.",
        )
    return company_id


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def require_company_admin_access(
    request: Request,
    x_api_key: str | None = Header(default=None, alias=API_KEY_HEADER),
    x_company_id: str | None = Header(default=None, alias=COMPANY_ID_HEADER),
    authorization: str | None = Header(default=None, alias=AUTHORIZATION_HEADER),
) -> None:
    """Allow either the global admin key or a scoped company bearer token."""
    expected_api_key = settings.admin_api_key
    if not expected_api_key and not settings.company_admin_token_secret:
        return

    if expected_api_key and x_api_key and compare_digest(x_api_key, expected_api_key):
        return

    company_id = x_company_id or getattr(request.state, "company_id", None) or settings.default_company_id
    bearer_token = _extract_bearer_token(authorization)
    if bearer_token and company_id and verify_company_admin_token(bearer_token, company_id):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing company admin credentials.",
    )


def assign_request_id(request: Request) -> str:
    """Reuse a caller-supplied request ID or generate one for tracing."""
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
    request.state.request_id = request_id
    return request_id
