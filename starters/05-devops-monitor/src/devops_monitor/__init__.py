"""
Module: devops_monitor
Description: Intelligent DevOps monitoring with health checks, diagnostics, and multi-channel alerts.

Implements:
    - docs/sdk/commands.md#the-command-decorator
    - docs/sdk/integrations.md#llm-integration
    - docs/sdk/integrations.md#email-integration
    - docs/sdk/integrations.md#telegram-integration
    - docs/sdk/integrations.md#http-integration
"""

from devops_monitor.commands import alert, diagnose, health_check, status_report

__all__ = ["health_check", "diagnose", "alert", "status_report"]
