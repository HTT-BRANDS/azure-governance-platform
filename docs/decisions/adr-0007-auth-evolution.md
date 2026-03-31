---
status: accepted
date: 2025-02-15
decision-makers: Solutions Architect 🏛️, Security Auditor 🛡️, Pack Leader 🐺
consulted: Code Puppy 🐶 (implementation), Experience Architect 🎨 (UX flow)
informed: All engineering teams, MSP administrators
relates-to: AUTH-001, AUTH-002, AUTH-003
---

# Authentication Architecture Evolution: Phase A→B→C

## Context and Problem Statement

The Azure Governance Platform requires secure authentication to protect sensitive Azure resource data, compliance findings, and multi-tenant configurations. As the platform evolved from proof-of-concept to production-ready SaaS, our authentication architecture needed to evolve across three distinct phases to meet increasing security requirements while maintaining operational simplicity.

**Phase A Challenge**: Initial implementation used hardcoded client secrets in environment variables. This created security risks (secrets in logs), operational friction (manual rotation), and blocked production deployment.

**Phase B Challenge**: Single-tenant application with manually configured federated credentials required per-customer Azure AD app registrations. This didn't scale for MSPs managing 5+ customer tenants.

**Phase C Challenge**: Full zero-secrets architecture required to eliminate credential management overhead completely and achieve true production security posture.

How should the authentication architecture evolve to meet production security standards while enabling multi-tenant SaaS operations?

## Decision Drivers

- **Security (K.O. criterion)**: Zero secrets in code, configuration, or CI/CD pipelines; no credentials accessible to humans
- **Operational scalability**: MSP scenario requires same app registration to authenticate across 5+ customer tenants without per-tenant configuration
- **Compliance**: Must align with SOC2, ISO 27001, and customer security audit requirements
- **Implementation velocity**: Each phase must be deployable incrementally without full rearchitecture
- **Backward compatibility**: Existing deployments must migrate smoothly between phases
- **Azure native alignment**: Leverage Azure's authentication capabilities rather than building custom systems

## Considered Options

1. **Phase A: Client Secrets** — Traditional OAuth2 client credentials with long-lived secrets
2. **Phase B: Federated Credentials (Single Tenant)** — OIDC federation with GitHub Actions, per-tenant app registrations
3. **Phase C: Federated Credentials (Multi-Tenant + Zero Secrets)** — OIDC federation with User-Assigned Managed Identity, no secrets anywhere

## Decision Outcome

**Chosen approach: Three-phase evolution (A→B→C)**, implemented incrementally over 6 months:

- **Phase A** (Jan 2025): Single-tenant with client secrets — quick to implement, acceptable for staging only
- **Phase B** (Feb 2025): Single-tenant with OIDC federation — eliminates secrets from CI/CD, enables automated deployments
- **Phase C** (Mar 2025): Multi-tenant with User-Assigned Managed Identity — zero secrets architecture, production-ready

Each phase builds on the previous, with explicit migration paths and validation gates. Phase A→B migration completed February 2025. Phase B→C migration completed March 2025.

### Phase A: Client Secrets Architecture

**Implementation**:
```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│ Application │────▶│ Client ID   │────▶│ Azure AD        │
│             │     │ + Secret    │     │ Token Endpoint  │
└─────────────┘     └─────────────┘     └─────────────────┘
```

- Azure AD application registration with client secret
- Secret stored in GitHub Secrets or environment variables
- Direct client credentials flow for token acquisition
- Suitable for: Development, staging environments with short-lived deployments

**Limitations**: Secrets require rotation, can be leaked in logs, human-accessible in CI/CD.

### Phase B: Single-Tenant Federated Credentials

**Implementation**:
```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│ GitHub      │────▶│ OIDC Token  │────▶│ Azure AD        │
│ Actions     │     │ (ephemeral) │     │ Federated Creds │
└─────────────┘     └─────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ Trust Relationship: GitHub OIDC ▶ Azure AD App          │
│ No long-lived secrets in CI/CD                          │
└─────────────────────────────────────────────────────────┘
```

- OIDC federation between GitHub Actions and Azure AD
- Ephemeral tokens (15-minute lifetime)
- Single-tenant app registration
- Federated credentials configured for specific GitHub repos/branches

**Benefits**: Eliminates secrets from CI/CD, automated token lifecycle, auditable via Azure AD sign-in logs.

**Migration from Phase A**: `scripts/migrate-to-phase-b.sh` — configures federated credentials, validates token acquisition, retires client secrets.

### Phase C: Multi-Tenant Zero Secrets

**Implementation**:
```
┌─────────────┐     ┌─────────────────────────────┐     ┌─────────────────┐
│ Application │────▶│ User-Assigned Managed         │────▶│ Azure AD        │
│ (any Azure) │     │ Identity (UAMI)              │     │ Multi-Tenant App│
└─────────────┘     └─────────────────────────────┘     └─────────────────┘
         │
         │┌────────────────────────────────────────────────────────────────┐
         ││ GitHub Actions also uses UAMI for OIDC federation             │
         ││ → No secrets anywhere in the system                          │
         └┴────────────────────────────────────────────────────────────────┘
```

- Multi-tenant Azure AD application registration
- User-Assigned Managed Identity (UAMI) for runtime authentication
- OIDC federation via UAMI for CI/CD deployments
- Customer tenants grant admin consent once

**Benefits**: Zero secrets anywhere; no credential rotation; works across all customer tenants; production security posture.

**Migration from Phase B**: `scripts/migrate-to-phase-c.sh` — provisions UAMI, configures OIDC federation, validates multi-tenant access, removes all remaining secrets.

### Migration Path Summary

| Phase | Secrets | Federation | Multi-Tenant | Migration Command |
|-------|---------|------------|--------------|-------------------|
| A | Client secrets in env | None | No | N/A (baseline) |
| B | None | GitHub→Azure AD | No | `scripts/migrate-to-phase-b.sh` |
| C | None | UAMI-based | Yes | `scripts/migrate-to-phase-c.sh` |

### Consequences

**Good**:
- Progressive security improvement without big-bang rewrites
- Each phase is independently deployable and testable
- Full audit trail via Azure AD logs
- Eliminates credential rotation operational burden
- Meets enterprise security audit requirements

**Bad**:
- Three-phase evolution requires maintenance of migration scripts
- Customer tenants must grant admin consent for Phase C
- Phase B→C migration requires brief deployment window (covered by blue-green deployment)

### Confirmation

Validation gates between phases:

- **Phase A→B**: `scripts/verify-federated-creds.sh` validates token acquisition without secrets
- **Phase B→C**: `scripts/verify-tenant-access.ps1` validates multi-tenant connectivity
- Production checklist: `docs/security/production-audit.md`

## STRIDE Security Analysis

| Threat Category | Risk Level | Mitigation |
|-----------------|-----------|------------|
| **Spoofing** | Low | OIDC tokens are signed by GitHub/Microsoft identity providers; cryptographically verified by Azure AD |
| **Tampering** | Low | Token binding to specific workflow runs and commit SHAs; any tampering invalidates the token |
| **Repudiation** | Low | Azure AD sign-in logs record all federated credential authentications; GitHub Actions logs record OIDC token issuance |
| **Information Disclosure** | Low | Phase C achieves zero secrets — nothing to disclose; ephemeral tokens have 15-minute lifetime |
| **Denial of Service** | Medium | Azure AD token endpoint or GitHub OIDC provider outage could block deployments; mitigated by UAMI fallback for runtime |
| **Elevation of Privilege** | Low | Federated credentials have explicit trust relationships (repo, branch, environment); no credential sharing between environments |

**Overall Security Posture**: Phase C achieves defense-in-depth with no secrets in any layer of the stack. Ephemeral tokens, cryptographically bound to specific CI/CD contexts, provide the strongest authentication posture available on Azure.

## Pros and Cons of the Options

### Option 1: Stay on Client Secrets (Don't Evolve)

- Good, because no migration effort required
- Bad, because fails SOC2/ISO 27001 audit requirements
- Bad, because secret rotation is operational burden
- Bad, because secrets can leak in logs or be accessible to developers

### Option 2: Phase B Only (No Multi-Tenant)

- Good, because eliminates CI/CD secrets
- Bad, because doesn't scale to MSP scenario (5+ tenants)
- Bad, because still requires per-tenant app registrations
- Bad, because doesn't achieve zero-secrets at runtime

### Option 3: Phase C Direct (Skip Phase B)

- Good, because reaches target state immediately
- Bad, because higher initial complexity and risk
- Bad, because harder to debug if issues arise
- Bad, because no incremental validation checkpoints

## More Information

- Migration runbooks: `docs/runbooks/phase-b-multi-tenant-app.md`, `docs/runbooks/phase-c-zero-secrets.md`
- ACR→GHCR migration (related): `docs/runbooks/acr-to-ghcr-migration.md`
- Security audit: `docs/security/production-audit.md`
- Phase C setup script: `scripts/setup-uami-phase-c.sh`

---

**Template Version:** MADR 4.0 (September 2024) with STRIDE Security Analysis  
**Last Updated:** 2025-03-15  
**Maintained By:** Solutions Architect 🏛️
