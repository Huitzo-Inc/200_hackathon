"""
Module: lead_engine
Description: AI-powered lead scoring and outreach engine.

Implements:
    - docs/sdk/commands.md#the-command-decorator
    - docs/sdk/integrations.md#llm-integration
    - docs/sdk/integrations.md#email-integration
    - docs/sdk/integrations.md#http-integration
"""

from lead_engine.commands import add_lead, pipeline_report, score_lead, send_outreach

__all__ = ["add_lead", "score_lead", "send_outreach", "pipeline_report"]
