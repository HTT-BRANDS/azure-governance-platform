---
status: {proposed | rejected | accepted | deprecated | superseded by ADR-NNNN}
date: YYYY-MM-DD
decision-makers: {list everyone involved in the decision}
consulted: {list subject matter experts who provided input}
informed: {list stakeholders who were kept updated}
---

# {Short title of solved problem and solution, present tense imperative}

## Context and Problem Statement

{Describe the context and problem statement in 2-3 sentences or as an illustrative story. You may want to articulate the problem in form of a question and add links to collaboration boards or issue management systems.}

## Decision Drivers

- {decision driver 1, e.g., a force, facing concern, ...}
- {decision driver 2, e.g., a force, facing concern, ...}
- {etc.}

## Considered Options

- {title of option 1}
- {title of option 2}
- {title of option 3}
- {etc.}

## Decision Outcome

Chosen option: "{title of option 1}", because {justification. e.g., only option which meets k.o. criterion decision driver | which resolves force {force} | ... | comes out best (see below)}.

### Consequences

- Good, because {positive consequence, e.g., improvement of one or more desired qualities, ...}
- Bad, because {negative consequence, e.g., compromising one or more desired qualities, ...}
- {etc.}

### Confirmation

{Describe how the implementation of/compliance with the ADR is confirmed. E.g., by a review or an automated test. Although we classify this element as optional, it is included in most ADRs.}

## STRIDE Security Analysis

| Threat Category | Risk Level | Mitigation |
|-----------------|-----------|------------|
| **Spoofing** | {Low/Medium/High} | {How the decision addresses or mitigates spoofing threats} |
| **Tampering** | {Low/Medium/High} | {How the decision addresses or mitigates tampering threats} |
| **Repudiation** | {Low/Medium/High} | {How the decision addresses or mitigates repudiation threats} |
| **Information Disclosure** | {Low/Medium/High} | {How the decision addresses or mitigates information disclosure threats} |
| **Denial of Service** | {Low/Medium/High} | {How the decision addresses or mitigates DoS threats} |
| **Elevation of Privilege** | {Low/Medium/High} | {How the decision addresses or mitigates privilege escalation threats} |

**Overall Security Posture:** {Summary of how this decision impacts the overall security of the system}

## Pros and Cons of the Options

### {title of option 1}

{example | description | pointer to more information | ...}

- Good, because {argument a}
- Good, because {argument b}
- Neutral, because {argument c}
- Bad, because {argument d}
- {etc.}

### {title of option 2}

{example | description | pointer to more information | ...}

- Good, because {argument a}
- Good, because {argument b}
- Neutral, because {argument c}
- Bad, because {argument d}
- {etc.}

### {title of other options}

{etc.}

## More Information

{You might want to provide additional evidence/confidence for the decision outcome here and/or document the team agreement on the decision and/or define when this decision when and how the decision should be realized and if/when it should be re-visited and/or how the decision is validated. Links to other decisions and resources might also appear here.}

---

**Template Version:** MADR 4.0 (September 2024) with STRIDE Security Analysis  
**Last Updated:** {date}  
**Maintained By:** Solutions Architect 🏛️
