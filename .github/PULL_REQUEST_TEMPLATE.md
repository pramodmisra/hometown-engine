# Pull Request

## What this PR does

<!-- 1-2 sentences describing the change. -->

## Compliance checklist

**Every box must be checked before merge.** A feature that violates compliance is not a feature — it is a disqualification risk.

### NIL & individual data

- [ ] No individual athlete names appear in any UI output, log line, or API response
- [ ] No athlete photos or videos appear anywhere
- [ ] All API responses are aggregate (`GROUP BY region × sport`); no individual records leak past the ingestion layer

### Branding & IP

- [ ] No IOC marks anywhere (Olympic rings, torch, Agitos)
- [ ] No USOPC marks
- [ ] No corporate logos other than Google Cloud
- [ ] App title and copy do not use "Olympic Games" as a standalone product name

### Terminology

- [ ] No "former Olympian" or "past Olympian" anywhere — once an Olympian, always an Olympian
- [ ] Sport names use official terminology (e.g. "Swimming"), not NGB names (e.g. "USA Swimming")
- [ ] Games references follow approved patterns: "Olympic Games [City] [Year]", "Paralympic Games [City] [Year]", "LA28 Games"

### Conditional phrasing

- [ ] All Gemini system prompts require conditional language ("could help foster", "may be associated with")
- [ ] All static UI copy uses conditional phrasing — no "produces winners", "guarantees", "predicts performance"

### Data scope

- [ ] All data is filtered to Team USA / US scope only
- [ ] No finish times, no specific scoring results — only placement and medal counts
- [ ] Data sources are publicly available and used in compliance with their terms

### Olympic / Paralympic parity

- [ ] Olympic and Paralympic counts have identical visual treatment (font, color, chart size)
- [ ] Para sports are not behind a tab or toggle
- [ ] Adaptive infrastructure is surfaced as prominently as standard infrastructure

### Repo hygiene

- [ ] Apache 2.0 license remains visible in repo About section
- [ ] No secrets, API keys, or service account JSON committed
- [ ] No public sharing of project details outside the hackathon submission flow

## Test plan

<!-- How was this verified? Manual steps or automated tests. -->
