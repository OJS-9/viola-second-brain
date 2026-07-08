"""
Second Brain platform integrations (Phase 4).

Each module in this package follows one pattern: dataclass config -> auth ->
query functions -> format_for_context() -> register_cli(). See
integration_template.py for the documented reference shape, and registry.py
for how the CLI/heartbeat discover which integrations are configured.
"""
