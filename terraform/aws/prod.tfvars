lambda_name = "alaska-geoportal-mcp-prod"
stage_name  = "prod"
aws_region  = "us-west-2"
config_file = "config.yaml"
# 1024 MB: aggregate_by_polygon holds up to AGG_SOURCE_LIMIT source features in
# memory plus a bounded 32-entry polygon cache. Also buys more Lambda
# CPU, which accelerates the pure-Python point-in-polygon work.
lambda_memory = 1024
# Kept in sync with config.yaml, which WINS for this variable (main.tf reads
# `local.config.aws.lambda_timeout` first and only falls back to this var).
# 28s sits just under API Gateway's hard, non-adjustable 29s integration
# timeout so the Lambda self-terminates before the gateway gives up.
lambda_timeout  = 28
api_quota_limit = 3000
# Rate/burst feed BOTH the stage-wide throttle (the aggregate cap on the
# keyless public /mcp) and the usage-plan throttle (API-key traffic).
# Steady-state posture, restored 2026-08-23 after the ESRI UC week raise
# (2026-07-13 .. 2026-08-23 ran at 20 / 40); see docs/RUNBOOK.md.
api_rate_limit  = 5
api_burst_limit = 10
custom_domain   = "alaska-geoportal.codeforanchorage.org"

# Cap concurrent Lambda executions. Cost and blast-radius protection if
# WAF is bypassed via distributed sources. Conversational MCP traffic does
# not need horizontal scale; raise if legitimate users start getting throttled.
# Steady-state: 10, restored 2026-08-23 (ESRI UC week ran at 25). Bounds
# worst-case Lambda spend to ~10 GB-s/s ~= $14/day even at full saturation.
lambda_reserved_concurrency = 10

# WAF per-IP rate limit (rolling 5-minute window). The MCP tools are
# conversational, so 1 rps sustained per IP (~300/5min) is plenty for
# real users and tight enough to slow scrapers and denial-of-wallet probes.
# NOTE: ALL claude.ai users share ~5 Anthropic egress IPs (160.79.106.32/27),
# so this per-IP limit is effectively an aggregate cap on claude.ai traffic.
# Steady-state: 300, restored 2026-08-23 (ESRI UC week ran at 600).
# NOTE: INERT while use_shared_waf = true -- it only takes effect on a
# rollback to a dedicated ACL. The LIVE per-IP limit lives in mcp-stats'
# `fleet_waf_members` under key `alaska-geoportal` and must be set to 300
# THERE as well, or the effective WAF cap stays at 600.
# TODO(go-live): add an `alaska-geoportal` key to mcp-stats
# `fleet_waf_members` BEFORE the first prod deploy -- with
# use_shared_waf = true and no fleet entry, this host has no per-IP rule.
waf_rate_limit_per_5min = 300

# CloudWatch alarms (errors, throttles, 5xx, probing, duration) notify this
# topic; email subscription on it. Empty string = alarms are dashboard-only.
# TODO(go-live): create the `alaska-geoportal-mcp-prod-alarms` SNS topic by
# hand (as was done for the Anchorage fork) and paste its ARN here.
alarm_sns_topic_arn = ""

# Hardened, API-key-gated /mcp-gcc route for an M365 GCC Copilot consumer.
# Off for this fork: no GCC consumer has been identified for the statewide
# server. Flip to true and retrieve the key with
# `terraform output -raw gcc_api_key_value` if one appears.
enable_gcc_route = false

# Use the fleet-wide WAF instead of a dedicated ACL for this MCP. A dedicated
# ACL costs ~$8/mo in fixed AWS charges regardless of traffic; the shared ACL
# keeps this MCP's 600/5min limit as its own counter, aggregated on
# (IP, Host) so it stays independent of the other MCPs sharing that limit.
#
# The effective limit now lives in mcp-stats' `fleet_waf_members` under the key
# `alaska-geoportal` (TODO: add that key before go-live, see above) --
# change it there, not here. The rate-limit value above is retained
# so that rolling back (use_shared_waf = false) restores the original limit.
# See mcp-stats/docs/waf-consolidation.md.
use_shared_waf = true
