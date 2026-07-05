"""
PreToolUse hook: Block access to sensitive files and environment variables.

Intercepts Read, Bash, Grep, Glob, Edit, and Write tool calls to prevent API
keys, tokens, and credentials from entering the LLM context window.

Zero third-party imports (json, re, sys only) — runs via bare `python`, not
`uv run`, because it fires on every single tool call and must be fast.

Baseline for Phase 2 — hardened and tested in Phase 8.

Exit codes:
  0 = allow (tool proceeds normally)
  2 = block (stderr shown to Claude as feedback)
"""

import json
import re
import sys

# --- Sensitive file patterns ---
# Any file path matching these patterns should never be read or written by the LLM
SENSITIVE_FILE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\.env($|\.)", re.IGNORECASE),  # .env, .env.local, .env.production
    re.compile(r"\.pem$", re.IGNORECASE),  # SSL/TLS certificates
    re.compile(r"\.key$", re.IGNORECASE),  # Private keys
    re.compile(r"credentials.*\.json", re.IGNORECASE),  # credentials.json, credentials_x.json
    re.compile(r".*token.*\.json", re.IGNORECASE),  # any *token*.json
    re.compile(r"\.ssh/", re.IGNORECASE),  # SSH keys directory
    re.compile(r"id_rsa", re.IGNORECASE),  # SSH private key
    re.compile(r"id_ed25519", re.IGNORECASE),  # SSH private key (ed25519)
    re.compile(r"\.netrc", re.IGNORECASE),  # Network credentials
    re.compile(r"secret", re.IGNORECASE),  # Files with "secret" in the name
]

# Exclude false positives for the "secret" pattern — these are safe to read
SECRET_FALSE_POSITIVES: list[re.Pattern[str]] = [
    re.compile(r"\.md$", re.IGNORECASE),
    re.compile(r"\.py$", re.IGNORECASE),
    re.compile(r"\.txt$", re.IGNORECASE),
    re.compile(r"\.example$", re.IGNORECASE),
]


def is_sensitive_file(path: str) -> str | None:
    """Check if a file path matches a sensitive pattern. Returns the reason or None."""
    if not path:
        return None

    # .env.example is always allowed, regardless of which pattern matched
    lower_path = path.lower()
    if ".env.example" in lower_path:
        return None

    for pattern in SENSITIVE_FILE_PATTERNS:
        if pattern.search(path):
            if pattern.pattern == "secret":
                if any(fp.search(path) for fp in SECRET_FALSE_POSITIVES):
                    continue
            return f"Blocked: '{path}' matches sensitive file pattern '{pattern.pattern}'"
    return None


# --- Dangerous bash patterns for env/secret exposure ---
DANGEROUS_BASH_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Direct .env / credentials / key reads
    (re.compile(r"\bcat\b.*\.env\b", re.IGNORECASE), "Reading .env file with cat"),
    (re.compile(r"\bhead\b.*\.env\b", re.IGNORECASE), "Reading .env file with head"),
    (re.compile(r"\btail\b.*\.env\b", re.IGNORECASE), "Reading .env file with tail"),
    (re.compile(r"\btype\b.*\.env\b", re.IGNORECASE), "Reading .env file with type"),
    (re.compile(r"\bcat\b.*credentials", re.IGNORECASE), "Reading credentials file"),
    (re.compile(r"\bcat\b.*token", re.IGNORECASE), "Reading token file"),
    (re.compile(r"\bcat\b.*\.pem\b", re.IGNORECASE), "Reading certificate file"),
    (re.compile(r"\bcat\b.*\.key\b", re.IGNORECASE), "Reading key file"),
    (re.compile(r"\bcat\b.*id_rsa", re.IGNORECASE), "Reading SSH private key"),
    (re.compile(r"\bcat\b.*id_ed25519", re.IGNORECASE), "Reading SSH private key"),
    (re.compile(r"\bcat\b.*\.ssh/", re.IGNORECASE), "Reading SSH directory file"),
    (re.compile(r"\btype\b.*credentials", re.IGNORECASE), "Reading credentials file (Windows type)"),
    # Environment variable printing
    (re.compile(r"\bprintenv\b", re.IGNORECASE), "Printing environment variables"),
    (re.compile(r"\benv\b\s*$", re.IGNORECASE), "Listing all environment variables"),
    (re.compile(r"\benv\b\s*\|", re.IGNORECASE), "Piping environment variables"),
    (re.compile(r"\bset\b\s*\|", re.IGNORECASE), "Piping shell variables"),
    (re.compile(r"\$env:\w*\s*\|", re.IGNORECASE), "Piping PowerShell environment variables"),
    (re.compile(r"Get-ChildItem\s+env:", re.IGNORECASE), "Listing PowerShell environment variables"),
    # Echo/printf of specific secret-like variables
    (
        re.compile(
            r"\becho\b.*\$.*(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API_KEY|ACCESS_TOKEN|AUTH)",
            re.IGNORECASE,
        ),
        "Echoing secret environment variable",
    ),
    (
        re.compile(r"\$env:\w*(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", re.IGNORECASE),
        "Referencing secret PowerShell environment variable",
    ),
    # Python inline execution that accesses env vars
    (re.compile(r"python[3]?\s+-c\s+.*os\.environ", re.IGNORECASE), "Python inline code accessing os.environ"),
    (re.compile(r"python[3]?\s+-c\s+.*os\.getenv", re.IGNORECASE), "Python inline code accessing os.getenv"),
    (re.compile(r"python[3]?\s+-c\s+.*dotenv", re.IGNORECASE), "Python inline code loading dotenv"),
    (re.compile(r"python[3]?\s+-c\s+.*\.env", re.IGNORECASE), "Python inline code referencing .env"),
    # Grep/search targeting sensitive files
    (re.compile(r"\bgrep\b.*\.env\b", re.IGNORECASE), "Grep searching .env file"),
    (re.compile(r"\brg\b.*\.env\b", re.IGNORECASE), "Ripgrep searching .env file"),
]


def check_bash_command(command: str) -> str | None:
    """Check if a bash command would expose secrets. Returns the reason or None."""
    normalized = " ".join(command.split()).strip()

    for pattern, reason in DANGEROUS_BASH_PATTERNS:
        if pattern.search(normalized):
            return f"Blocked: {reason}"

    # Check inside $(...) and `...` subshells too
    for sp in (re.compile(r"\$\((.*?)\)", re.DOTALL), re.compile(r"`(.*?)`", re.DOTALL)):
        for match in sp.finditer(normalized):
            result = check_bash_command(match.group(1))
            if result:
                return f"{result} (inside subshell)"

    return None


# --- Content-based checks: scripts that would print/exfiltrate secrets once written ---
EXFILTRATION_CONTENT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"print\s*\(.*os\.environ", re.IGNORECASE), "Script prints os.environ to stdout"),
    (re.compile(r"print\s*\(.*os\.getenv\s*\(", re.IGNORECASE), "Script prints os.getenv() to stdout"),
    (re.compile(r"open\s*\(.*\.env.*\).*read\(\)", re.IGNORECASE), "Script reads .env file contents"),
    (re.compile(r"cat\s+.*\.env", re.IGNORECASE), "Script cats .env file"),
    (
        re.compile(r"echo\s+\$\{?[A-Z_]*(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", re.IGNORECASE),
        "Script echoes secret variable",
    ),
    (re.compile(r"printenv", re.IGNORECASE), "Script runs printenv"),
]


def check_written_content(content: str) -> str | None:
    """Check if file content being written would exfiltrate secrets."""
    if not content:
        return None
    for pattern, reason in EXFILTRATION_CONTENT_PATTERNS:
        if pattern.search(content):
            return f"Blocked: {reason} — writing scripts that expose secrets is not allowed"
    return None


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("Failed to parse hook input JSON", file=sys.stderr)
        sys.exit(1)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {}) or {}

    reason: str | None = None

    if tool_name == "Read":
        reason = is_sensitive_file(tool_input.get("file_path", ""))

    elif tool_name == "Bash":
        reason = check_bash_command(tool_input.get("command", ""))

    elif tool_name == "Grep":
        path = tool_input.get("path", "")
        if path:
            reason = is_sensitive_file(path)
        if not reason and re.search(r"\.env", path or "", re.IGNORECASE):
            reason = "Blocked: Grep targeting .env file"

    elif tool_name in ("Edit", "Write"):
        reason = is_sensitive_file(tool_input.get("file_path", ""))
        if not reason:
            content = tool_input.get("content", "") or tool_input.get("new_string", "")
            reason = check_written_content(content)

    elif tool_name == "Glob":
        pattern_str = tool_input.get("pattern", "")
        if re.search(r"\.env", pattern_str, re.IGNORECASE):
            reason = "Blocked: Glob pattern targeting .env files"

    if reason:
        print(f"SECURITY: {reason}. API keys and credentials must never enter the context window.", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
