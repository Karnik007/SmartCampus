"""Server-side social provider token verification."""

from __future__ import annotations

import requests
from django.core.exceptions import ValidationError


GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"
FACEBOOK_ME_URL = "https://graph.facebook.com/me"
TIMEOUT = 10


def verify_social_token(provider: str, access_token: str | None = None, id_token: str | None = None) -> dict:
    """Validate provider tokens and return canonical user payload."""
    if provider == "google":
        return _verify_google(id_token=id_token, access_token=access_token)
    if provider == "github":
        return _verify_github(access_token)
    if provider == "facebook":
        return _verify_facebook(access_token)
    raise ValidationError("Unsupported social provider.")


def _verify_google(id_token: str | None = None, access_token: str | None = None) -> dict:
    token_param = {"id_token": id_token} if id_token else {"access_token": access_token}
    resp = requests.get(GOOGLE_TOKENINFO_URL, params=token_param, timeout=TIMEOUT)
    if resp.status_code != 200:
        raise ValidationError("Invalid Google token.")

    data = resp.json()
    email = data.get("email")
    if not email:
        raise ValidationError("Google account did not return an email.")

    return {
        "email": email,
        "name": data.get("name") or data.get("given_name") or email.split("@")[0],
        "provider_id": data.get("sub", ""),
        "avatar_url": data.get("picture", ""),
    }


def _verify_github(access_token: str | None) -> dict:
    if not access_token:
        raise ValidationError("GitHub access token is required.")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }
    user_resp = requests.get(GITHUB_USER_URL, headers=headers, timeout=TIMEOUT)
    if user_resp.status_code != 200:
        raise ValidationError("Invalid GitHub token.")
    user_data = user_resp.json()

    email = user_data.get("email")
    if not email:
        emails_resp = requests.get(GITHUB_EMAILS_URL, headers=headers, timeout=TIMEOUT)
        if emails_resp.status_code == 200:
            emails = emails_resp.json()
            primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
            if primary:
                email = primary.get("email")
            elif emails:
                email = emails[0].get("email")

    if not email:
        raise ValidationError("GitHub account did not return an email.")

    return {
        "email": email,
        "name": user_data.get("name") or user_data.get("login") or email.split("@")[0],
        "provider_id": str(user_data.get("id") or ""),
        "avatar_url": user_data.get("avatar_url", ""),
    }


def _verify_facebook(access_token: str | None) -> dict:
    if not access_token:
        raise ValidationError("Facebook access token is required.")

    params = {"fields": "id,name,email,picture", "access_token": access_token}
    resp = requests.get(FACEBOOK_ME_URL, params=params, timeout=TIMEOUT)
    if resp.status_code != 200:
        raise ValidationError("Invalid Facebook token.")
    data = resp.json()

    email = data.get("email")
    if not email:
        raise ValidationError("Facebook account did not return an email.")

    picture = ((data.get("picture") or {}).get("data") or {}).get("url", "")
    return {
        "email": email,
        "name": data.get("name") or email.split("@")[0],
        "provider_id": data.get("id", ""),
        "avatar_url": picture,
    }
