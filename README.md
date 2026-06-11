# Growth MCP

<p align="left">
  <img src="https://img.shields.io/github/v/release/thaolst/growth-mcp?label=version&color=4ade80&style=flat-square" alt="version" />
  <img src="https://img.shields.io/github/license/thaolst/growth-mcp?color=60a5fa&style=flat-square" alt="license" />
  <img src="https://img.shields.io/github/last-commit/thaolst/growth-mcp?color=a78bfa&style=flat-square" alt="last commit" />
  <img src="https://img.shields.io/github/stars/thaolst/growth-mcp?style=flat-square&color=facc15&logo=github" alt="stars" />
  <img src="https://img.shields.io/badge/language-VI%20%2B%20EN-blue?style=flat-square" alt="language" />
</p>

> MCP server cho growth marketing - đóng gói domain knowledge thành tools Claude có thể gọi trực tiếp trong chat.

# Tiếng Việt

## Giải quyết vấn đề gì?

Growth PM thường mất thời gian làm đi làm lại các phân tích lặp: tính drop rate từ cohort data, nhớ intervention nào phù hợp budget nào, tra công thức sample size, design voucher theo segment...

**growth-mcp** đóng gói những logic này lại. Claude gọi trực tiếp trong chat, trả kết quả có thể dùng ngay - không còn trả lời chung chung.

## Minh hoạ thực tế

### 1. Phân tích retention cohort

**Bạn hỏi:**
> "Cohort tháng 3: week_0=100%, week_1=62%, week_2=41%, week_3=28%, week_4=21%. Budget nhỏ. Phân tích giúp mình."

**Claude trả lời:**
> Drop lớn nhất ở **W0→W1: 38%** - đây là early activation problem, không phải retention problem. Retention về sau (W1→W2: 33.9%, W2→W3: 31.7%) thực ra khá ổn định.
>
> Với budget S, nên tập trung vào W0→W1 trước:
> - In-app push reminder trong 24h đầu
> - Time-based trigger: nếu chưa quay lại sau 3 ngày → send offer
> - Streak mechanic nhỏ: visit 3 ngày liên tiếp = reward

### 2. Design campaign + voucher

**Bạn hỏi:**
> "Muốn reactivate lapsed users (inactive 30-60 ngày, từng order ≥3 lần). Budget khoảng 100M. Nên làm gì?"

**Claude trả lời:**
> **Campaign level M** - budget 50-200M VND, timeline 2-4 tuần. Channels: in-app push + paid social.
>
> Với lapsed segment có lịch sử order tốt:
> - **Fixed discount 40-50%**, không min spend
> - Expiry **48 giờ** - tạo urgency, không để họ "để mai"

### 3. Churn risk + điểm thưởng

**Bạn hỏi:**
> "Segment này 45 ngày chưa active, 12.000 users, trung bình còn 320 điểm chưa dùng. Nguy cơ thế nào?"

**Claude trả lời:**
> **Medium risk** - đang tiến gần ngưỡng churn. 320 điểm tích luỹ là hook tốt: nhắc điểm sắp hết hạn kết hợp offer nhỏ hiệu quả hơn discount đơn thuần.

### 4. Đọc kết quả A/B test

**Bạn hỏi:**
> "Control 847 convert / 10.000 users, treatment 923 / 10.000. Có nên launch không?"

**Claude trả lời:**
> Control: 8.47% → Treatment: 9.23% (+8.97% lift). Nhưng **p = 0.058 → chưa significant**.
>
> Chưa nên launch. Cần thêm data. Nếu launch sớm, 6% chance đây là noise.

### 5. Tính sample size trước khi chạy test

**Bạn hỏi:**
> "Conversion rate hiện tại 3.2%, muốn detect được lift 15%. Cần bao nhiêu users?"

**Claude trả lời:**
> Cần **30.307 users/variant**, tổng **60.614 users** (power 90%, α=5%). Plan traffic trước, không chạy rồi mới tính.

## Cài đặt

```bash
git clone https://github.com/thaolst/growth-mcp.git
cd growth-mcp
pip install -e .
```

## Dùng với Claude Desktop

Thêm vào config file:
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

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

Restart Claude Desktop → chat bình thường, Claude tự gọi tool khi cần.

## Dùng với Cursor

Thêm vào `.cursor/mcp.json`:

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

## Tools

| Tool | Làm gì | Input chính |
|---|---|---|
| `design_campaign` | Brief campaign theo level S/M/L | level, objective, segment |
| `suggest_voucher` | Voucher phù hợp segment | segment, objective, budget_level |
| `optimize_voucher` | Voucher ladder 3 bậc kèm abuse risk | avg_order_value_vnd, target_conversion_lift_pct, budget_per_user_vnd, voucher_type |
| `inspect_csv` | Xem cấu trúc file CSV: cột, kiểu dữ liệu, sample | file_path |
| `analyze_experiment_from_csv` | A/B test trực tiếp từ CSV raw (1 dòng/user) | file_path, group_col, converted_col |
| `analyze_retention_from_csv` | Phân tích cohort retention từ CSV (rate hoặc count) | file_path, period_col, value_col |
| `summarize_segments_from_csv` | Thống kê theo segment từ CSV raw | file_path, segment_col, value_col |
| `analyze_experiment_from_bigquery` | A/B test trên kết quả SQL BigQuery | sql, group_col, converted_col |
| `analyze_retention_from_bigquery` | Retention cohort từ BigQuery | sql, period_col, value_col |
| `summarize_segments_from_bigquery` | Thống kê segment trên warehouse data | sql, segment_col, value_col |
| `analyze_experiment_from_mixpanel` | A/B test từ event Mixpanel | exposure_event, conversion_event, group_property, from_date, to_date |
| `summarize_segments_from_mixpanel` | Thống kê segment trên event Mixpanel | event, segment_property, value_property, from_date, to_date |
| `monitor_campaign` | **Monitor campaign real-time** | run_days, reach, redemptions, vouchers, budget |
| `analyze_segment` | **Phân tích segment + recommend targeting** | segment_type, size, retention, redemption |
| `analyze_retention` | Phân tích cohort, tìm điểm drop | cohort_data (JSON), campaign_level |
| `predict_churn_risk` | Đánh giá nguy cơ churn | days_inactive, users, points |
| `analyze_experiment` | Đọc kết quả A/B test | control/treatment counts + sample sizes |
| `estimate_sample_size` | Tính sample size trước khi test | baseline_rate, MDE |

## Hệ sinh thái repo

Mình có 3 repo phục vụ 3 mục đích khác nhau:

| Repo | Là gì | Dùng khi nào |
|---|---|---|
| [ai-growth-prompts](https://github.com/thaolst/ai-growth-prompts) | Thư viện prompt theo chủ đề, copy-paste được ngay | Cần prompt cho 1 task cụ thể: thiết kế voucher, phân tích segment, viết brief |
| [ai-growth-agents-for-marketers](https://github.com/thaolst/ai-growth-agents-for-marketers) | Workflow nhiều bước dạng prompt + script, có skill cài cho Claude Code | Muốn chạy quy trình end-to-end: lập kế hoạch MEU, phân tích A/B test |
| [growth-mcp](https://github.com/thaolst/growth-mcp) (repo này) | MCP server đóng gói logic growth thành tool | Muốn Claude/Cursor gọi tool trực tiếp thay vì paste prompt |


Tool BigQuery cần extra dependency và auth chuẩn Google Cloud:

```bash
pip install "growth-mcp[bigquery]"
gcloud auth application-default login
```

Chỉ chấp nhận query SELECT (read-only), giới hạn 200K dòng. Data lớn hơn thì aggregate ngay trong SQL.

Tool Mixpanel không cần thêm dependency, chỉ cần API secret của project:

```bash
export MIXPANEL_API_SECRET=your_secret
# EU data residency: export MIXPANEL_API_HOST=data-eu.mixpanel.com
```

Khoảng thời gian export giới hạn 90 ngày, 200K event.

## Knowledge layer (prompts + resources)

Ngoài tools, server còn đóng gói domain knowledge theo chuẩn MCP, mỗi entry có version và source trace (field = từ campaign thật, standard = chuẩn ngành):

| Loại | Tên | Nội dung |
|---|---|---|
| Resource | `growth://frameworks` | Retention benchmark theo tuần, nguyên tắc voucher ladder, cấu trúc lập kế hoạch MEU, checklist experiment hygiene |
| Resource | `growth://glossary` | Thuật ngữ growth dùng xuyên suốt các tool: MEU, voucher ladder, cohort, abuse risk |
| Prompt | `ab_test_readout` | Workflow đọc kết quả test: phân tích data, check hygiene checklist, viết readout dưới 250 từ |
| Prompt | `meu_campaign_plan` | Lập kế hoạch MEU tháng: decompose target, đọc data trước, gán mechanic theo segment |
| Prompt | `voucher_design_review` | Review thiết kế voucher theo từng nguyên tắc ladder kèm abuse risk |

## Giới hạn

Các tool phân tích nhận data qua tham số hoặc qua data layer CSV (`*_from_csv`). Đã hỗ trợ CSV, BigQuery và Mixpanel. Nguồn khác thì export ra CSV rồi phân tích. Giúp **tư duy nhanh hơn**, không thay thế data analyst.

## 👤 Tác giả

**Le Song Tien Thao (Tara)** - Growth Marketer. Xây prompts, bots, và workflows cho growth marketing thực chiến.

🔗 [LinkedIn](https://linkedin.com/in/thaolst) · [Facebook](https://www.facebook.com/LeSongTienThao) · [X](https://x.com/thaolst) · [Substack](https://thaolst.substack.com/) · [Email](mailto:tienthaotara@gmail.com)

*Nếu repo này hữu ích, [star nhé](https://github.com/thaolst/growth-mcp) ⭐*

# Growth MCP

> MCP server for growth marketing - packaging domain knowledge into tools Claude can call directly in chat.

## What problem does it solve?

Growth PMs often spend time repeating the same analyses: calculating drop rates from cohort data, remembering which interventions fit which budget, looking up sample size formulas, designing vouchers by segment...

**growth-mcp** packages this logic so Claude can call it directly in chat and return actionable output - not generic advice.

## Real examples

### 1. Retention cohort analysis

**You ask:**
> "March cohort: week_0=100%, week_1=62%, week_2=41%, week_3=28%, week_4=21%. Small budget. Analyse this."

**Claude responds:**
> Biggest drop at **W0→W1: 38%** - this is an early activation problem, not a retention problem. Later-stage retention (W1→W2: 33.9%, W2→W3: 31.7%) is actually quite stable.
>
> With a small budget, focus on W0→W1 first:
> - In-app push reminder within the first 24h
> - Time-based trigger: if no return after 3 days → send offer
> - Simple streak mechanic: visit 3 days in a row = reward

### 2. Campaign design + voucher

**You ask:**
> "I want to reactivate lapsed users (inactive 30-60 days, had ≥3 orders). Budget around 100M. What should I do?"

**Claude responds:**
> **Campaign level M** - budget 50-200M VND, timeline 2-4 weeks. Channels: in-app push + paid social.
>
> For a lapsed segment with a strong order history:
> - **Fixed discount 40-50%**, no min spend
> - Expiry **48 hours** - creates urgency

### 3. Churn risk + loyalty points

**You ask:**
> "This segment hasn't been active for 45 days, 12,000 users, average 320 unused points. How at risk are they?"

**Claude responds:**
> **Medium risk** - approaching the churn threshold. 320 accumulated points are a strong hook: reminding them their points are expiring combined with a small offer works better than a standalone discount.

### 4. Reading A/B test results

**You ask:**
> "Control: 847 conversions / 10,000 users. Treatment: 923 / 10,000. Should I launch?"

**Claude responds:**
> Control: 8.47% → Treatment: 9.23% (+8.97% lift). But **p = 0.058 → not significant**.
>
> Don't launch yet. Need more data. If you launch now, there's a 6% chance this is noise.

### 5. Sample size before running a test

**You ask:**
> "Current conversion rate is 3.2%, I want to detect a 15% lift. How many users do I need?"

**Claude responds:**
> You need **30,307 users/variant**, total **60,614 users** (90% power, α=5%). Plan your traffic allocation before running, not after.

## Installation

```bash
git clone https://github.com/thaolst/growth-mcp.git
cd growth-mcp
pip install -e .
```

## Use with Claude Desktop

Add to your config file:
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

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

Restart Claude Desktop → chat normally, Claude calls tools automatically when needed.

## Use with Cursor

Add to `.cursor/mcp.json`:

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

## Tools

| Tool | What it does | Key inputs |
|---|---|---|
| `design_campaign` | Campaign brief by level S/M/L | level, objective, segment |
| `suggest_voucher` | Voucher recommendation by segment | segment, objective, budget_level |
| `optimize_voucher` | 3-tier voucher ladder with abuse risk | avg_order_value_vnd, target_conversion_lift_pct, budget_per_user_vnd, voucher_type |
| `inspect_csv` | Inspect CSV structure: columns, types, sample | file_path |
| `analyze_experiment_from_csv` | A/B test straight from raw CSV (1 row/user) | file_path, group_col, converted_col |
| `analyze_retention_from_csv` | Retention cohort analysis from CSV (rates or counts) | file_path, period_col, value_col |
| `summarize_segments_from_csv` | Per-segment stats from raw CSV | file_path, segment_col, value_col |
| `analyze_experiment_from_bigquery` | A/B test on a BigQuery SQL result | sql, group_col, converted_col |
| `analyze_retention_from_bigquery` | Retention cohort from BigQuery | sql, period_col, value_col |
| `summarize_segments_from_bigquery` | Segment stats on warehouse data | sql, segment_col, value_col |
| `analyze_experiment_from_mixpanel` | A/B test from Mixpanel events | exposure_event, conversion_event, group_property, from_date, to_date |
| `summarize_segments_from_mixpanel` | Segment stats over Mixpanel events | event, segment_property, value_property, from_date, to_date |
| `analyze_retention` | Cohort analysis, find biggest drop point | cohort_data (JSON), campaign_level |
| `predict_churn_risk` | Assess churn risk level | days_inactive, users, points |
| `analyze_experiment` | Read A/B test results with stats | control/treatment counts + sample sizes |
| `estimate_sample_size` | Calculate sample size before running a test | baseline_rate, MDE |

## Repo ecosystem

I maintain 3 repos serving different purposes:

| Repo | What it is | When to use |
|---|---|---|
| [ai-growth-prompts](https://github.com/thaolst/ai-growth-prompts) | Topic-based prompt library, ready to copy-paste | You need a prompt for one specific task: voucher design, segment analysis, campaign brief |
| [ai-growth-agents-for-marketers](https://github.com/thaolst/ai-growth-agents-for-marketers) | Multi-step workflows as prompts + scripts, installable as Claude Code skills | You want an end-to-end process: MEU planning, A/B test analysis |
| [growth-mcp](https://github.com/thaolst/growth-mcp) (this repo) | MCP server packaging growth logic as callable tools | You want Claude/Cursor to call tools directly instead of pasting prompts |


BigQuery tools need the optional dependency and standard Google Cloud auth:

```bash
pip install "growth-mcp[bigquery]"
gcloud auth application-default login
```

Read-only (SELECT queries only), capped at 200K rows. Aggregate in SQL for bigger data.

Mixpanel tools need no extra dependency, just your project API secret:

```bash
export MIXPANEL_API_SECRET=your_secret
# EU data residency: export MIXPANEL_API_HOST=data-eu.mixpanel.com
```

Export window capped at 90 days, 200K events.

## Knowledge layer (prompts + resources)

Beyond tools, the server packages domain knowledge through standard MCP primitives. Every entry is versioned and source-traced (field = distilled from real campaigns, standard = industry methodology):

| Type | Name | Content |
|---|---|---|
| Resource | `growth://frameworks` | Weekly retention benchmarks, voucher ladder principles, MEU planning structure, experiment hygiene checklist |
| Resource | `growth://glossary` | Growth terms used across the tools: MEU, voucher ladder, cohort, abuse risk |
| Prompt | `ab_test_readout` | Test readout workflow: analyze the data, check the hygiene checklist, write a readout under 250 words |
| Prompt | `meu_campaign_plan` | Monthly MEU planning: decompose the target, read data first, assign mechanics per segment |
| Prompt | `voucher_design_review` | Review a voucher design against each ladder principle with abuse risk |

## Limitations

Analysis tools take data via parameters or through the CSV data layer (`*_from_csv`). CSV, BigQuery, and Mixpanel are supported. For other sources, export to CSV first, then analyze. Meant to **speed up thinking**, not replace a data analyst.

## 👤 Author

**Le Song Tien Thao (Tara)** - Growth Marketer. Building prompts, bots, and workflows for real growth marketing work.

🔗 [LinkedIn](https://linkedin.com/in/thaolst) · [Facebook](https://www.facebook.com/LeSongTienThao) · [X](https://x.com/thaolst) · [Substack](https://thaolst.substack.com/) · [Email](mailto:tienthaotara@gmail.com)

*If this is useful, [star the repo](https://github.com/thaolst/growth-mcp) ⭐*

## License

MIT - use freely, share widely.
