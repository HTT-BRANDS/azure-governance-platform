# Control Tower Internal Rebrand Plan

**Date:** 2026-04-30  
**Branch:** `control-tower-internal-rebrand`  
**Decision:** Tyler selected **Control Tower** as the internal product/repo name.

> This plan intentionally treats **Control Tower** as an internal HTT product
> name. It acknowledges the AWS Control Tower collision but accepts that risk for
> internal use. If the product is ever marketed externally, reopen naming and run
> formal trademark/legal diligence. Tiny lawyer hat still not included.

---

## 1. Naming decision

| Item | Decision |
|---|---|
| Product/display name | **Control Tower** |
| GitHub repo target slug | `control-tower` |
| Package/project target name | `control-tower` |
| Existing Azure resource names | Keep as-is for now (`app-governance-prod`, `rg-governance-production`, etc.) |
| Existing bd issue prefix | Keep as-is (`azure-governance-platform-*`) |
| Existing historical docs | Preserve, but add/current docs should clarify that Control Tower is now accepted for internal use. |
| External/commercial use | Requires separate legal/name clearance. |

---

## 2. Why not rename every operational identifier?

Some strings are identity/branding. Others are operational contracts.
Confusing those is how outages sneak in wearing a fake mustache.

### Rename / update now

- README title and introductory framing.
- `pyproject.toml` package metadata and project URLs.
- App startup log / docstring display name.
- Current status, onboarding, runbook, RTO/RPO, continuity docs.
- Strategic plan D-Name section.
- GitHub issue-template links once repo slug changes.
- GitHub Pages workflow/test defaults once repo slug changes.
- Docs that describe the platform as "Portfolio Platform" or "Azure Governance Platform" when referring to product identity.

### Do not rename without a dedicated infrastructure migration

- Azure resource groups: `rg-governance-*`.
- Azure App Services: `app-governance-*`.
- SQL servers/databases/key vaults/storage accounts.
- Existing image tags already deployed from `ghcr.io/htt-brands/azure-governance-platform`.
- Historical release evidence that cites old repo/image names.
- bd issue IDs / JSONL history.

---

## 3. Repo rename cutover checklist

When ready to rename the GitHub repository from
`HTT-BRANDS/azure-governance-platform` to `HTT-BRANDS/control-tower`:

1. Confirm no production deploy is in progress.
2. Rename the GitHub repository:
   ```bash
   gh repo rename control-tower --repo HTT-BRANDS/azure-governance-platform --yes
   ```
3. Update local remote:
   ```bash
   git remote set-url origin https://github.com/HTT-BRANDS/control-tower.git
   ```
4. Decide GHCR strategy:
   - Short-term safest: continue pulling `ghcr.io/htt-brands/azure-governance-platform` until the next deploy image is proven.
   - Clean target: workflows push/pull `ghcr.io/htt-brands/control-tower`.
5. If moving GHCR path, update GitHub Actions environment variables:
   - `.github/workflows/deploy-staging.yml`
   - `.github/workflows/deploy-production.yml`
   - `.github/workflows/container-registry-migration.yml`
   - `.github/actions/verify-production-image/README.md` examples
   - `env-delta.yaml`
   - `infrastructure/parameters*.json`
6. Dispatch staging deploy and verify:
   - CI
   - Security Scan
   - Deploy to Staging
   - Pages deploy
   - Pages browser tests at the new URL
7. Dispatch production deploy only after staging proves the new image path.
8. Update external docs/links from old slug to new slug.
9. Keep a rollback path:
   - GitHub usually redirects old repo URLs after rename.
   - GHCR path migration may not be transparent. Keep old image references until new path is verified.

---

## 4. Collision / caveat language

Use this language in internal docs where needed:

> Control Tower is HTT's internal name for this platform. It is unrelated to AWS
> Control Tower. Do not use this name for external commercialization without a
> separate naming/legal review.

---

## 5. Recommended implementation sequence

1. Product/display-name pass on current docs/code metadata.
2. Project/package metadata pass.
3. Repo-link pass using `control-tower` target slug.
4. Workflow/GHCR pass only when the repo rename and image path cutover are
   intentionally scheduled.
5. Infrastructure resource rename is explicitly out of scope unless there is a
   business reason stronger than "it looks nicer."

YAGNI says do not rename stable Azure resources just to satisfy a brand itch.
Azure will absolutely make that itch expensive.
