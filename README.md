# OpportunityGuard

An AI agent that investigates suspicious job offers and recruitment messages before someone shares personal information or pays money.

Think of a person in Bengaluru who receives a WhatsApp message:
Congratulations! You have been selected for an AI Engineer position. Pay ₹2,500 for registration and verification to receive your offer letter.

The person doesn't know whether the offer is genuine. They might search Google, check LinkedIn, ask friends, or simply trust the message.

Existing scam checkers may identify suspicious wording, but the person needs more than a warning. They need evidence about the company, the job posting, the sender, and the requested payment.
The exact problem to solve
Job seekers cannot easily verify the authenticity of a job offer by checking all the relevant evidence in one place.

Your target users would be:
- Freshers applying for their first jobs.
- Experienced professionals looking to switch jobs.
- Students receiving internship offers.
- Job seekers receiving recruitment messages through WhatsApp, Telegram, email, and LinkedIn.
Your initial target market should be Indian job seekers, with Bengaluru as your first user-testing location.
The solution
Build an AI agent that accepts a job description, recruitment message, company name, sender email, or job URL and conducts a structured investigation.

It should perform five tasks:
1. Message analysis: Identify suspicious requests for money, urgency, unrealistic salaries, requests for OTPs, and other common fraud indicators.
2. Company verification: Check whether the company appears to exist and whether its official website and contact details can be established.
3. Recruitment verification: When evidence is accessible, compare the supplied job posting with the company's official careers page or other authoritative sources.
4. Risk assessment: Explain which warning signs were found and which checks could not be completed.
5. Next-step guidance: Tell the user what to verify independently before proceeding.
The result should be an evidence-based assessment, not just an AI-generated guess.