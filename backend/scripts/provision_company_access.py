"""Provision or rotate a company portal access key through the backend API."""

from __future__ import annotations

import argparse
import os
import secrets
import sys

import requests


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or rotate a company access key using the backend API."
    )
    parser.add_argument(
        "--api-base-url",
        default=os.getenv("BACKEND_API_BASE_URL", "http://127.0.0.1:8000"),
        help="Backend base URL, for example https://your-backend-domain.onrender.com",
    )
    parser.add_argument(
        "--admin-api-key",
        default=os.getenv("ADMIN_API_KEY"),
        help="Master admin API key for provisioning access.",
    )
    parser.add_argument("--company-id", required=True, help="Company workspace ID, for example acme-dental")
    parser.add_argument(
        "--company-access-key",
        help="Explicit company access key. If omitted, a secure random key is generated.",
    )
    parser.add_argument("--display-name", help="Human-friendly company name shown in the portal.")
    parser.add_argument(
        "--answer-mode",
        choices=("sales", "support", "portfolio"),
        help="Assistant tone preset for the company.",
    )
    parser.add_argument("--chatbot-title", help="Portal and widget title for this company.")
    parser.add_argument("--chatbot-subtitle", help="Portal and widget subtitle for this company.")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=20.0,
        help="Request timeout in seconds.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.admin_api_key:
        parser.error("--admin-api-key is required, or set ADMIN_API_KEY in the environment.")

    company_access_key = args.company_access_key or secrets.token_urlsafe(24)
    endpoint = f"{args.api_base_url.rstrip('/')}/api/company-access"

    payload = {
        "company_id": args.company_id,
        "company_access_key": company_access_key,
    }
    if args.display_name:
        payload["display_name"] = args.display_name
    if args.answer_mode:
        payload["answer_mode"] = args.answer_mode
    if args.chatbot_title:
        payload["chatbot_title"] = args.chatbot_title
    if args.chatbot_subtitle:
        payload["chatbot_subtitle"] = args.chatbot_subtitle

    try:
        response = requests.put(
            endpoint,
            headers={
                "X-API-Key": args.admin_api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=args.timeout_seconds,
        )
    except requests.RequestException as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    try:
        body = response.json()
    except ValueError:
        body = {"detail": response.text.strip() or "Unknown error."}

    if response.status_code >= 400:
        print(
            f"Provisioning failed with status {response.status_code}: {body.get('detail', 'Unknown error.')}",
            file=sys.stderr,
        )
        return 1

    print("Company access provisioned successfully.")
    print(f"Company ID: {body.get('company_id', args.company_id)}")
    print(f"Company access key: {company_access_key}")
    profile = body.get("profile") or {}
    if profile.get("display_name"):
        print(f"Display name: {profile['display_name']}")
    print(f"Backend API: {args.api_base_url.rstrip('/')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
