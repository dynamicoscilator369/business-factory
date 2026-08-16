# Grok Bot context — {{BUSINESS_NAME}}

Project: {{WORKSPACE}}/project/company-kernel
Business id: {{BUSINESS_ID}}

## Pipeline (workers)

```bash
cd {{WORKSPACE}}/project/company-kernel && ./run-pipeline.sh {{BUSINESS_ID}}
```

Handoff: `businesses/{{BUSINESS_ID}}/.state/handoff.json`

## Your job

Read `businesses/{{BUSINESS_ID}}/manifest.json` for seat definitions.
{{SEAT_JOB}}

## Rules

- Metrics come from scorecard tools — never invent numbers
- Escalate money/people/policy to human Visionary
- Secrets in Grok Bot Secrets, never chat
- Turkey / priority channels first if configured in manifest
