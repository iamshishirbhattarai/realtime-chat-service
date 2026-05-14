from pathlib import Path

import firebase_admin
from firebase_admin import credentials

from app.core.config import settings

_firebase_app: firebase_admin.App | None = None


def get_firebase_app() -> firebase_admin.App:
    global _firebase_app
    if _firebase_app is None:
        if not settings.firebase_credentials_path:
            raise ValueError("Firebase credentials path is not set.")

        cred = credentials.Certificate(
            str(Path(settings.firebase_credentials_path).expanduser())
        )
        _firebase_app = firebase_admin.initialize_app(cred)

    return _firebase_app
