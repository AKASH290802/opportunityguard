'''Chat protocol and ASI:One investigation logic for OpportunityGuard AI.'''

import json
import os
import re
from datetime import datetime, timezone
from uuid import uuid4

from openai import OpenAI
from uagents import Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

from http_client import gather_evidence

protocol = Protocol(spec=chat_protocol_spec)

# Agentverse injects ASI1_BASE_URL and ASI1_API_KEY into every hosted agent.
client = OpenAI(
    base_url=os.environ['ASI1_BASE_URL'],
    api_key=os.environ['ASI1_API_KEY'],
)

HELP_TEXT = (
    'I investigate job offers and recruitment messages before you pay money or share '
    'personal details.\n\n'
    'Paste the full message you received (WhatsApp, Telegram, email or LinkedIn) and I will:\n'
    '1. Extract the company, role, payment request and sender details\n'
    '2. Check the company and any links against live web evidence\n'
    '3. Give you a risk verdict with India-specific verification steps\n\n'
    "Tip: include the sender's name, the company name, any links and the exact wording "
    'of any payment request.'
)

EXTRACTION_PROMPT = (
    'You extract structured facts from job or recruitment messages for a scam-checking '
    'service in India. Return ONLY a JSON object, no explanations, using these keys '
    '(fill with "" or [] when a fact is absent, never invent values):\n'
    '{"company": "", "role": "", "payment_amount": "", "payment_reason": "", '
    '"contact_channel": "", "sender_identifier": "", "salary": "", "urls": [], '
    '"urgency_flags": []}\n'
    'Definitions: company = organisation or HR firm named in the message; role = job '
    'title offered; payment_amount = any money requested, with currency; '
    'payment_reason = stated reason for the payment; contact_channel = '
    'whatsapp/telegram/email/linkedin/phone/website; sender_identifier = email, phone '
    'or handle of the sender; salary = offered pay; urls = every URL or domain in the '
    'message; urgency_flags = short quotes showing urgency, secrecy or pressure.'
)

ANALYST_PROMPT = (
    'You are OpportunityGuard AI, a job-offer scam investigator for Indian job seekers '
    '(students, freshers and experienced professionals, Bengaluru first). You receive '
    'the pasted recruitment message, extracted facts and evidence from live web '
    'checks.\n\n'
    'Write the investigation report in Markdown with exactly these sections:\n'
    '1. **Verdict** - one line: 🔴 HIGH RISK / 🟠 CAUTION / 🟢 LOW RISK plus one '
    'sentence explaining why.\n'
    '2. **Red flags** - bullets, each with a short why-it-matters note. Indian '
    'job-scam patterns to check: any upfront fee (registration, verification, security '
    'deposit, training kit, laptop or documentation fee), interviews or offers only '
    'via WhatsApp/Telegram, an offer without any real interview, HR writing from free '
    'email domains, salary unrealistic for the role or experience level, urgency or '
    'secrecy pressure, requests for OTP/bank details/Aadhaar/PAN before a verified '
    'offer, links on domains that do not match the company name.\n'
    '3. **Evidence check** - summarise the live web results about the company and '
    'whether any linked website loaded (status, page title). If evidence is empty, say '
    'the company has no verifiable online footprint and treat that as a warning sign, '
    'not proof.\n'
    '4. **How to verify yourself** - concrete India-specific steps: MCA company search '
    'on mca.gov.in, the official careers page, a LinkedIn recruiter check, calling the '
    'official HR number from the company\'s own website (never a number from the '
    'message), and Glassdoor/AmbitionBox plus Reddit/Quora complaint searches.\n'
    '5. **Do this now** - 3-5 short actions. Always include: never pay any fee for a '
    'job or internship - legitimate employers never charge money at any stage; never '
    'share OTP, bank details, Aadhaar or documents until the employer is verified.\n\n'
    'Rules: base every claim on the message, the extracted facts or the evidence - '
    'never invent company facts; if the evidence contradicts the red flags, say so; '
    'calm, protective, practical tone; under 450 words; reply in the user\'s language '
    '(default English). If the user asks a general question instead of pasting an '
    'offer, answer it helpfully with the same scam-awareness guidance instead of '
    'forcing the report format.'
)

FALLBACK_REPORT = (
    '⚠️ I could not complete the full analysis right now, but the most important '
    'guidance always applies: **never pay any fee for a job offer** - registration, '
    'verification, training-kit or security-deposit requests are the most common '
    'Indian job-scam pattern.\n\n'
    '**Do this now**\n'
    '- Verify the company on the MCA portal (mca.gov.in) and its official careers page\n'
    '- Call the HR number listed on the company\'s own website, never one from the message\n'
    '- Never share OTP, bank details, Aadhaar or documents until the employer is verified\n\n'
    'Please try sending the offer message again in a moment.'
)


def create_text_chat(text):
    content = [TextContent(type='text', text=text)]
    return ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=content)


def _parse_json(raw):
    match = re.search(r'\{.*\}', raw, flags=re.S)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _extract_facts(message_text):
    completion = client.chat.completions.create(
        model='asi1-mini',
        messages=[
            {'role': 'system', 'content': EXTRACTION_PROMPT},
            {'role': 'user', 'content': message_text[:4000]},
        ],
        max_tokens=600,
    )
    return _parse_json(completion.choices[0].message.content or '')


def _looks_like_offer(facts, message_text):
    if (
        facts.get('company')
        or facts.get('role')
        or facts.get('payment_amount')
        or facts.get('urls')
    ):
        return True
    return len(message_text.split()) >= 12


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id,
        ),
    )

    text = msg.text()
    if not text:
        return

    facts = {}
    try:
        facts = _extract_facts(text)
    except Exception:
        ctx.logger.exception('Fact extraction with ASI:One failed')

    if not _looks_like_offer(facts, text):
        await ctx.send(sender, create_text_chat(HELP_TEXT))
        return

    await ctx.send(
        sender,
        create_text_chat(
            '🔍 Investigation started - extracting offer details, checking the company '
            'and links against live web evidence. This takes a few seconds...'
        ),
    )

    company = str(facts.get('company') or '').strip()
    urls = [str(url).strip() for url in (facts.get('urls') or []) if str(url).strip()][:3]
    evidence = gather_evidence(company, urls)

    user_content = (
        'RECRUITMENT MESSAGE (verbatim):\n<<<\n'
        + text[:4000]
        + '\n>>>\n\n'
        + 'EXTRACTED FACTS (JSON):\n'
        + json.dumps(facts, ensure_ascii=False)
        + '\n\nLIVE EVIDENCE (JSON from web checks, may be empty):\n'
        + json.dumps(evidence, ensure_ascii=False)[:6000]
    )

    try:
        completion = client.chat.completions.create(
            model='asi1',
            messages=[
                {'role': 'system', 'content': ANALYST_PROMPT},
                {'role': 'user', 'content': user_content},
            ],
            max_tokens=2000,
        )
        report = (completion.choices[0].message.content or '').strip()
    except Exception:
        ctx.logger.exception('ASI:One analysis failed')
        report = FALLBACK_REPORT

    if not report:
        report = FALLBACK_REPORT

    await ctx.send(sender, create_text_chat(report))


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass
