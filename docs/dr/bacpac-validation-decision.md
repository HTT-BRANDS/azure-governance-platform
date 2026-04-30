# BACPAC Export Validation Decision

> **Status:** Decision required
> **Tracked by:** bd `azure-governance-platform-cz89`
> **Owner:** Tyler Granlund
> **Context:** Weekly BACPAC workflow exists, but staging validation is blocked
> because Azure SQL Free edition does not support ImportExport.

---

## 1. Problem

`cz89` added `.github/workflows/bacpac-export.yml` to complement Azure SQL
Basic 7-day PITR with long-term BACPAC exports to Azure Blob cool tier.

The implementation passed local checks, but acceptance requires one successful
staging run before enabling/trusting production schedule. Staging currently uses
Azure SQL Free edition, and Azure SQL ImportExport returns
`UnSupportedImportExportEdition` for that edition.

That means this is not an agent coding problem anymore; it is an environment /
risk decision.

---

## 2. Options

| Option | Description | Pros | Cons | Recommendation |
|---|---|---|---|---|
| A | Temporarily upgrade staging SQL to Basic/S0, run BACPAC validation, then downgrade if desired | Validates exact workflow against staging; low code churn | Requires Azure change; temporary cost; must avoid leaving staging upgraded accidentally | Recommended if Tyler wants staging-first validation |
| B | Provision a separate non-Free validation DB just for export testing | Avoids touching staging app DB | More infra; more secrets/cleanup; easy to leave zombie resources | Good if staging must remain Free |
| C | Validate directly against production with explicit risk acceptance | Fastest; validates real target | Riskier; export operation touches prod DB and storage; acceptance bypasses staging-first principle | Only if Tyler explicitly accepts risk |
| D | Revise acceptance and keep blocked | No Azure action | Long-term backup remains unverified | Acceptable short-term only |

---

## 3. Decision

| Field | Value |
|---|---|
| Selected option | 🔴 TODO Tyler |
| Decision date | 🔴 TODO Tyler |
| Decision maker | Tyler Granlund |
| Risk accepted? | 🔴 TODO |
| Rollback / cleanup required | 🔴 TODO |
| Evidence run ID | 🔴 TODO |

---

## 4. Option A runbook — temporary staging upgrade

Use this only if Tyler selects Option A.

```bash
# 1. Capture current staging SQL edition/objective.
az sql db show \
  --resource-group rg-governance-staging \
  --server sql-governance-staging-77zfjyem \
  --name governance \
  --query '{edition:edition, objective:currentServiceObjectiveName, status:status}' \
  --output json

# 2. Upgrade to an ImportExport-supported tier.
#    Choose the cheapest acceptable non-Free tier available in the subscription.
az sql db update \
  --resource-group rg-governance-staging \
  --server sql-governance-staging-77zfjyem \
  --name governance \
  --edition Basic \
  --service-objective Basic

# 3. Dispatch staging BACPAC workflow.
gh workflow run bacpac-export.yml --ref main -f environment=staging

# 4. Watch and record run ID.
gh run list --workflow=bacpac-export.yml --limit 5

# 5. Verify blob exists in the configured container and Cool tier is applied.
#    Use outputs from the workflow run; do not paste storage keys in docs.

# 6. Decide whether to downgrade staging back to Free.
#    If downgrading, capture the exact command and result here.
```

### Option A cleanup checklist

- [ ] Evidence run ID recorded in §3.
- [ ] Blob existence verified.
- [ ] Blob tier verified as Cool.
- [ ] Teams notification behavior verified or explicitly waived.
- [ ] Staging SQL tier restored or cost impact accepted.
- [ ] bd `cz89` updated with evidence.

---

## 5. Option B runbook — separate validation DB

Use this only if Tyler selects Option B.

High-level steps:

1. Provision a small non-Free Azure SQL DB in a temporary resource group or the
   staging resource group.
2. Seed it with harmless test schema/data, not production data.
3. Add workflow variables/secrets or a temporary workflow dispatch target.
4. Run export.
5. Verify blob and tier.
6. Delete the validation DB/resource group.
7. Record evidence and cleanup.

Do not implement this unless Tyler explicitly selects it; otherwise YAGNI, and
YAGNI is not a suggestion, it is a survival strategy.

---

## 6. Option C runbook — direct production validation

Use this only if Tyler explicitly selects Option C and accepts the risk.

Risk statement to record before dispatch:

> Tyler accepts running Azure SQL ImportExport against production before staging
> validation because staging Free edition cannot validate the operation. The
> expected impact is an online logical export to Blob storage; if the run fails,
> the platform still has Azure SQL PITR but no verified long-term export.

Then:

```bash
gh workflow run bacpac-export.yml --ref main -f environment=production
gh run list --workflow=bacpac-export.yml --limit 5
```

Record the run ID in §3 and update bd `cz89` only after success is verified.

---

## 7. Current status

As of 2026-04-30:

- Workflow exists.
- Local workflow contract validation passed in prior commits.
- Staging validation is blocked by Azure SQL Free ImportExport limitation.
- `cz89` is intentionally marked `blocked` with label
  `blocked-by-azure-sql-free` so it does not appear in `bd ready` as autonomous
  work.

---

*Authored by Richard (code-puppy-661ed0), 2026-04-30. No validation path was
selected on Tyler's behalf.*
