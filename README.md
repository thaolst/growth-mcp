# Growth MCP

MCP server for growth marketing — campaign design, retention analysis, churn prediction, A/B testing.

Built from battle-tested prompts used in live growth campaigns at MoMo (40M+ users).

## Tools

| Tool | Description | Inputs |
|------|-------------|--------|
| `design_campaign` | Generate campaign brief by level | level (S/M/L), objective, segment |
| `suggest_voucher` | Voucher design by segment | segment, objective, budget level |
| `analyze_retention` | Analyze cohort retention data | cohort_data (JSON), campaign_level |
| `predict_churn_risk` | Predict churn & recommend intervention | days_active, users, points |
| `analyze_experiment` | A/B test with statistical analysis | control/treatment metrics + samples |
| `estimate_sample_size` | Calculate required sample size | baseline_rate, MDE |

## Install

```bash
# Install from source
git clone https://github.com/thaolst/growth-mcp.git
cd growth-mcp
pip install -e .
```

## Use with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "growth-mcp": {
      "command": "python",
      "args": ["-m", "growth_mcp.server"]
    }
  }
}
```

## Use with Cursor

```bash
cursor --mcp-install growth-mcp
```

Or add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "growth-mcp": {
      "command": "python",
      "args": ["-m", "growth_mcp.server"]
    }
  }
}
```

## Examples

```
design_campaign(level="S", objective="Increase MAU by 10%",
                target_segment="New users, active <30 days")

analyze_retention(cohort_data='{"week_0":1.0,"week_1":0.68,"week_2":0.45,"week_3":0.32}')

analyze_experiment(control_metric=120, treatment_metric=145,
                   control_sample=1000, treatment_sample=1000)
```

## License

MIT — free to use, modify, and distribute.
