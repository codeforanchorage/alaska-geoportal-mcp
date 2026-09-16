# Deployment Guide

How the Alaska Geoportal MCP server is deployed to AWS. Operations after
deployment (kill switch, traffic postures, alarms, logs) are in the
[Runbook](RUNBOOK.md).

## What exists

One stack, in account `420839047325`, region `us-west-2`, Terraform
workspace `alaska-geoportal-prod`:

| Resource | Name |
|---|---|
| Lambda (python3.11, x86_64) | `alaska-geoportal-mcp-prod` |
| API Gateway REST API + stage | `ae6gj7yvfg`, stage `prod` |
| Custom domain | `alaska-geoportal.codeforanchorage.org` (ACM cert, regional) |
| WAF | associated with the fleet web ACL `mcp-fleet-waf` (owned by the mcp-stats repo) |
| CloudWatch | `/aws/lambda/alaska-geoportal-mcp-prod`, `/aws/apigateway/alaska-geoportal-mcp-prod-access`, alarms → SNS `alaska-geoportal-mcp-prod-alarms` |
| Terraform state | S3 `alaska-geoportal-opencontext-tfstate`, lock table `terraform-state-lock` (shared across the fleet) |

There is **no staging stack**. The parent repo removed it; `deploy.sh -e
staging` has no tfvars to run with.

## Prerequisites

- AWS CLI configured for the account (an IAM user with Lambda, API Gateway,
  IAM, CloudWatch, WAF-association, ACM and S3-state permissions)
- Terraform >= 1.0
- Python 3.11+ with `pip` (the packaging step cross-installs wheels for
  `manylinux2014_x86_64` / CPython 3.11, so any host Python works)

## Deploy

```bash
./scripts/deploy.sh -e prod
```

The script:

1. Validates `config.yaml` (exactly one plugin enabled, timeouts sane).
2. Builds the Lambda zip: `core/`, `plugins/`, `server/`, `config.yaml`,
   and `requirements.txt` dependencies installed for the Lambda platform.
3. Copies the zip and `config.yaml` into `terraform/aws/`, selects the
   workspace, runs `terraform plan` with `prod.tfvars`, prints a summary,
   and waits for an explicit `yes` before `terraform apply`.
4. Prints `api_gateway_url` and, when the custom domain is bound,
   `custom_domain_target`.

Afterwards:

```bash
SMOKE_URL=https://alaska-geoportal.codeforanchorage.org/mcp python scripts/smoke_prod.py
```

## Configuration facts that bite

- **`config.yaml` ships inside the zip.** The Lambda reads it from
  `$LAMBDA_TASK_ROOT`. It is *not* passed through the `OPENCONTEXT_CONFIG`
  environment variable (Terraform sets that to `""`), because Lambda caps
  env vars at 4 KB and the `instructions` block alone is larger.
- **`terraform/aws/config.yaml` is a build artifact.** `deploy.sh`
  overwrites it every run; it is gitignored. A bare `terraform plan` in
  `terraform/aws/` without the packaging step reads the stale copy.
- **`lambda_memory` and `lambda_timeout` come from `config.yaml`**, not
  from `prod.tfvars` (see `locals` in `main.tf`). `lambda_name` is the
  other way round.
- **Timeout ladder:** API Gateway integration 29 s (hard limit) >
  `lambda_timeout` 28 s > plugin HTTP `timeout` 20 s. Keep that order or a
  hung upstream turns into an opaque 502 instead of a readable tool error.

```yaml
aws:
  region: "us-west-2"
  lambda_name: "alaska-geoportal-mcp-staging"   # prod name comes from prod.tfvars
  lambda_memory: 1024                           # aggregate_by_polygon holds up to 5000 features
  lambda_timeout: 28
```

## Custom domain: first-time order of operations

`custom_domain.tf` creates the ACM certificate *and* binds an API Gateway
domain name to it. API Gateway refuses a certificate that is not yet
ISSUED, and issuance needs a DNS validation CNAME, so a brand-new stack
cannot be created in one apply with `custom_domain` set. The order that
works (done 2026-09-15 for this stack):

1. Deploy with `custom_domain = ""` in the working copy of `prod.tfvars`
   (don't commit that), then restore the file.
2. `terraform -chdir=terraform/aws apply -var-file=prod.tfvars
   -var=config_file=config.yaml -target=aws_acm_certificate.mcp_cert`, then
   read `acm_validation_cname_name` / `acm_validation_cname_value` from
   `terraform output` and add that CNAME in DNS.
3. When `aws acm describe-certificate` reports ISSUED, run the normal
   `./scripts/deploy.sh -e prod`. It binds the domain and prints
   `custom_domain_target`; add a CNAME from the hostname to that.

DNS for `codeforanchorage.org` is managed by hand (Dreamhost), not by
Terraform. Existing stacks with an issued certificate deploy in one step.

## Shared-fleet dependencies

- **WAF.** `use_shared_waf = true` in `prod.tfvars`: the stage is associated
  with the fleet ACL whose ARN is read from SSM. The per-host 300-per-5-min
  rate rule lives in the **mcp-stats** repo (`fleet_waf_members`, key
  `alaska-geoportal`) and must be applied there *before* a new host's first
  deploy, or the host is only covered by the catch-all rule.
- **Alarms SNS topic.** Created by CLI, outside Terraform; ARN in
  `prod.tfvars`. Email subscription must be confirmed from the inbox.
- **State bucket.** Created by CLI (`scripts/setup-backend.sh` or by hand),
  versioned, AES256, public access blocked. Must match `backend.tf`.

## Routes

| Path | Method | Backed by |
|---|---|---|
| `/mcp` | POST (and GET/DELETE/OPTIONS plumbing) | Lambda |
| `/` | GET | API Gateway MOCK landing page (`landing.tf`), no Lambda |
| `/mcp-gcc` | POST | only when `enable_gcc_route = true` (off here) |

## Traffic limits (steady state)

| Layer | Value | Where |
|---|---|---|
| API Gateway stage throttle | 5 rps, burst 10 | `api_rate_limit`, `api_burst_limit` |
| Lambda reserved concurrency | 10 | `lambda_reserved_concurrency` |
| WAF per IP per 5 min | 300 | mcp-stats `fleet_waf_members` |
| Usage-plan quota (API-key route only) | 3000/day | `api_quota_limit` |

Raising them for an event is a `prod.tfvars` edit plus deploy; see the
Runbook's traffic postures.

## Cost

At the Anchorage fork's observed traffic the stack runs at a few dollars a
month, dominated by CloudWatch logs; Lambda and API Gateway are cents. The
fleet-wide AWS Budget (`mcp-fleet-monthly`, tag `Project=mcp-server`) and
Cost Anomaly Detection cover this stack automatically via provider default
tags.

## Destroy

```bash
terraform -chdir=terraform/aws workspace select alaska-geoportal-prod
terraform -chdir=terraform/aws destroy -var-file=prod.tfvars -var=config_file=config.yaml
```

Leaves the state bucket, lock table, SNS topic and the mcp-stats WAF entry
in place; remove those by hand if the server is being retired for good.
