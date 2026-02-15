"""
Module: templates
Description: Email HTML templates for lead outreach.

Implements:
    - docs/sdk/integrations.md#email-integration
"""

from __future__ import annotations

from lead_engine.models import LeadRecord


def _base_html(body: str) -> str:
    """Wrap body content in a styled email layout."""
    return f"""\
<html>
<body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
{body}
<hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;">
<p style="font-size: 12px; color: #999;">
    Sent via Lead Engine | Powered by Huitzo
</p>
</body>
</html>"""


def render_intro(lead: LeadRecord) -> tuple[str, str]:
    """Render intro outreach email. Returns (subject, html_body)."""
    subject = f"Hi {lead.contact_name} - Quick intro from our team"
    body = f"""\
<p>Hi {lead.contact_name},</p>

<p>I came across <strong>{lead.company}</strong> and was impressed by what
you're building. I'd love to share how we help companies like yours
accelerate their workflows with intelligent automation.</p>

<p>Would you have 15 minutes this week for a quick call?</p>

<p>Best regards,<br>Your Sales Team</p>"""
    return subject, _base_html(body)


def render_follow_up(lead: LeadRecord) -> tuple[str, str]:
    """Render follow-up email. Returns (subject, html_body)."""
    subject = f"Following up - {lead.company}"
    body = f"""\
<p>Hi {lead.contact_name},</p>

<p>I wanted to follow up on my previous message. I understand things get
busy, but I genuinely believe we could add value to <strong>{lead.company}</strong>.</p>

<p>Here are a few quick wins our platform delivers:</p>
<ul>
    <li>AI-powered workflow automation</li>
    <li>Reduce manual data processing by 80%</li>
    <li>Real-time insights and reporting</li>
</ul>

<p>Happy to share a quick demo whenever works for you.</p>

<p>Best,<br>Your Sales Team</p>"""
    return subject, _base_html(body)


def render_demo_invite(lead: LeadRecord) -> tuple[str, str]:
    """Render demo invitation email. Returns (subject, html_body)."""
    subject = f"Exclusive demo for {lead.company}"
    body = f"""\
<p>Hi {lead.contact_name},</p>

<p>We'd love to give <strong>{lead.company}</strong> an exclusive look at our
platform in action. Our live demo covers:</p>

<ol>
    <li><strong>AI Intelligence Packs</strong> - See how AI makes decisions, not just follows rules</li>
    <li><strong>Multi-channel Integration</strong> - Email, HTTP, storage, all in one platform</li>
    <li><strong>Real-time Analytics</strong> - Track performance and optimize workflows</li>
</ol>

<p>The demo takes about 20 minutes and is completely personalized to your
use case.</p>

<p><a href="#" style="background: #2563eb; color: white; padding: 10px 20px;
text-decoration: none; border-radius: 5px; display: inline-block;">
Book Your Demo</a></p>

<p>Looking forward to connecting!</p>

<p>Best,<br>Your Sales Team</p>"""
    return subject, _base_html(body)


TEMPLATE_RENDERERS = {
    "intro": render_intro,
    "follow-up": render_follow_up,
    "demo-invite": render_demo_invite,
}
