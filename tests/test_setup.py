"""
Phase 1 verification script.
Checks that the folder structure exists and required packages are installed.
"""

import os
import sys

REQUIRED_DIRS = [
    "data/videos", "data/transcripts", "data/chunks", "data/metadata",
    "src/ingestion", "src/transcription", "src/chunking",
    "src/embeddings", "src/qdrant", "src/retrieval", "src/llm", "src/utils",
    "app/backend", "app/frontend",
    "scripts", "tests",
]

REQUIRED_PACKAGES = ["yt_dlp", "dotenv"]


def check_dirs():
    missing = [d for d in REQUIRED_DIRS if not os.path.isdir(d)]
    if missing:
        print("MISSING FOLDERS:")
        for m in missing:
            print(f"  - {m}")
        return False
    print("All folders present.")
    return True


def check_packages():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print("MISSING PACKAGES (pip install these):")
        for m in missing:
            print(f"  - {m}")
        return False
    print("All required packages importable.")
    return True


def check_env_file():
    if not os.path.exists(".env"):
        print("MISSING: .env file (copy .env.example to .env)")
        return False
    print(".env file present.")
    return True


if __name__ == "__main__":
    ok = True
    ok &= check_dirs()
    ok &= check_packages()
    ok &= check_env_file()

    if ok:
        print("\nPHASE 1 SETUP OK.")
        sys.exit(0)
    else:
        print("\nPHASE 1 SETUP INCOMPLETE. Fix the items above.")
        sys.exit(1)
