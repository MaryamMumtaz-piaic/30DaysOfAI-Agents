"""A demo inbox of unread emails so the agent can be tried without Gmail OAuth."""

SAMPLE_EMAILS = [
    {
        "id": 1,
        "from": "Sarah Chen <sarah.chen@acmecorp.com>",
        "subject": "URGENT: Production API is down for enterprise clients",
        "received": "8:42 AM",
        "body": (
            "Hi,\n\nOur monitoring just paged us — the payments API has been "
            "returning 503s for the last 20 minutes and three enterprise "
            "clients have already emailed asking what's going on. Can you jump "
            "on a call ASAP? We need an ETA for a fix and a holding statement "
            "we can send to customers.\n\nThanks,\nSarah\nVP Engineering"
        ),
    },
    {
        "id": 2,
        "from": "billing@awscloud-notices.com",
        "subject": "Your account has been suspended - verify payment now!!!",
        "received": "7:15 AM",
        "body": (
            "Dear Customer, Your cloud account will be TERMINATED in 24 hours "
            "unless you verify your billing details immediately. Click here to "
            "confirm your credit card and avoid data loss: http://aws-verify-"
            "account.xyz/login. Act now to keep your services online."
        ),
    },
    {
        "id": 3,
        "from": "Marcus Lee <marcus@designstudio.io>",
        "subject": "Re: Proposal for Q3 brand refresh",
        "received": "Yesterday, 6:30 PM",
        "body": (
            "Hi there,\n\nThanks for sending over the proposal — the team "
            "reviewed it and we're excited to move forward. Could you clarify "
            "the timeline for the first design milestone and whether revisions "
            "are included in the quoted price? Happy to sign this week once we "
            "align on those two points.\n\nBest,\nMarcus"
        ),
    },
    {
        "id": 4,
        "from": "TechCrunch Daily <newsletter@techcrunch.com>",
        "subject": "The 10 AI startups everyone's watching this week",
        "received": "Yesterday, 9:00 AM",
        "body": (
            "This week in tech: a roundup of the hottest AI startups, funding "
            "rounds, and product launches. Plus: our take on the latest model "
            "releases. Read online or unsubscribe at any time."
        ),
    },
    {
        "id": 5,
        "from": "Priya Nair <priya.nair@financepartners.com>",
        "subject": "Invoice #4821 — payment overdue by 15 days",
        "received": "Yesterday, 2:12 PM",
        "body": (
            "Hello,\n\nOur records show invoice #4821 for $12,400 is now 15 "
            "days past due. Please arrange payment by end of week to avoid a "
            "late fee. If payment has already been sent, kindly share the "
            "remittance advice.\n\nRegards,\nPriya, Accounts Receivable"
        ),
    },
    {
        "id": 6,
        "from": "Jordan Blake <jordan@meetupfriends.com>",
        "subject": "Coffee next week?",
        "received": "Monday, 11:20 AM",
        "body": (
            "Hey! It's been way too long. I'm in town next Thursday and Friday "
            "— any chance you're free to grab a coffee and catch up? No agenda, "
            "just would love to see you.\n\nCheers,\nJordan"
        ),
    },
]
