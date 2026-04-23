#!/usr/bin/env python3
"""
env-guard: PreToolUse security hook for Claude Code.

Blocks Claude from reading, writing, or shell-leaking sensitive credential
files (.env, AWS/Azure/GCP keys, SSH keys, database credentials, etc.).

Exit codes:
  0 = allow the operation
  2 = block the operation (stderr message sent back to Claude)
"""

import json
import os
import re
import sys

# Patterns for sensitive file paths (relative or absolute)
SENSITIVE_FILE_PATTERNS = [
    # dotenv files — but NOT .env.example / .env.sample / .env.template
    r"(^|/)\.env$",
    r"(^|/)\.env\.[^.]+$",
    # AWS credentials
    r"(^|/)\.aws/(credentials|config)$",
    r"(^|/)aws_credentials",
    # Azure / GCP service accounts
    r"(^|/)\.azure/",
    r"(^|/)gcloud/",
    r"(^|/)service[_-]?account.*\.json$",
    r"(^|/)credentials\.json$",
    # SSH private keys
    r"(^|/)\.ssh/(id_rsa|id_ed25519|id_ecdsa|id_dsa)$",
    r"(^|/)\.ssh/.*_key$",
    # Auth / package registry
    r"(^|/)\.netrc$",
    r"(^|/)\.pypirc$",
    r"(^|/)\.htpasswd$",
    # Database credentials
    r"(^|/)\.pgpass$",
    # Infrastructure secrets
    r"(^|/)terraform\.tfvars$",
    r"(^|/)secrets\.ya?ml$",
    # Shell history (may contain secrets from past commands)
    r"(^|/)\.(bash|zsh|fish)_history$",
]

# Allowlist: safe example/template files that should never be blocked
ALLOWLIST_PATTERNS = [
    r"\.env\.(example|sample|template|test|ci)$",
    r"\.env\.[^.]+\.(example|sample|template)$",
]

# Dangerous bash patterns that could leak secrets
DANGEROUS_BASH_PATTERNS = [
    r"\benv\b",           # bare `env` command dumps all vars
    r"\bprintenv\b",      # dumps env vars
    r"\bexport -p\b",     # dumps exported vars
    # cat of sensitive files
    r"cat\s+['\"]?.*\.env['\"]?(\s|$)",
    r"cat\s+['\"]?.*\.aws/credentials",
    r"cat\s+['\"]?.*id_rsa['\"]?",
    r"cat\s+['\"]?.*id_ed25519['\"]?",
    # echo of secret variables
    r"echo\s+\$[A-Z_]*(SECRET|KEY|PASSWORD|TOKEN|CREDENTIAL|PRIVATE)[A-Z_]*",
]

TOOL_FILE_PATH_KEYS = {
    "Read": "file_path",
    "Write": "file_path",
    "Edit": "file_path",
    "MultiEdit": "file_path",
}


def is_allowlisted(path: str) -> bool:
    return any(re.search(p, path, re.IGNORECASE) for p in ALLOWLIST_PATTERNS)


def is_sensitive_file(path: str) -> bool:
    if is_allowlisted(path):
        return False
    return any(re.search(p, path, re.IGNORECASE) for p in SENSITIVE_FILE_PATTERNS)


def is_dangerous_bash(command: str) -> bool:
    return any(re.search(p, command, re.IGNORECASE) for p in DANGEROUS_BASH_PATTERNS)


def block(reason: str) -> None:
    print(reason, file=sys.stderr)
    sys.exit(2)


def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        event = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        # On parse failure, allow (avoid false-positive friction)
        sys.exit(0)

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    # File-based tools
    if tool_name in TOOL_FILE_PATH_KEYS:
        file_path = tool_input.get(TOOL_FILE_PATH_KEYS[tool_name], "")
        if file_path and is_sensitive_file(file_path):
            block(
                f"[env-guard] Blocked: '{file_path}' matches a sensitive credential pattern.\n"
                "To allow access, add a permissions.allow rule in .claude/settings.json:\n"
                f'  {{ "permission": "allow", "tool": "{tool_name}", "path": "{file_path}" }}'
            )

    # Bash tool
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if command and is_dangerous_bash(command):
            block(
                f"[env-guard] Blocked: command matches a pattern that could expose secrets.\n"
                "Command preview: " + command[:120] + "\n"
                "To allow this command, add a permissions.allow rule in .claude/settings.json."
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
