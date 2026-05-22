# Growth MCP

MCP server cho growth marketing — đóng gói domain knowledge thành tools Claude có thể gọi trực tiếp trong chat.

---

## Giải quyết vấn đề gì?

Growth PM thường mất thời gian làm đi làm lại các phân tích lặp: tính drop rate từ cohort data, nhớ intervention nào phù hợp budget nào, tra công thức sample size, design voucher theo segment...

**growth-mcp** đóng gói những logic này lại. Claude gọi trực tiếp trong chat, trả kết quả có thể dùng ngay — không còn trả lời chung chung.

---

## Minh hoạ thực tế

### 1. Phân tích retention cohort

**Bạn hỏi:**
> "Cohort tháng 3: week_0=100%, week_1=62%, week_2=41%, week_3=28%, week_4=21%. Budget nhỏ. Phân tích giúp tôi."

**Claude trả lời:**
> Drop lớn nhất ở **W0→W1: 38%** — đây là early activation problem, không phải retention problem. Retention về sau (W1→W2: 33.9%, W2→W3: 31.7%) thực ra khá ổn định.
>
> Với budget S, nên tập trung vào W0→W1 trước:
> - In-app push reminder trong 24h đầu
> - Time-based trigger: nếu chưa quay lại sau 3 ngày → send offer
> - Streak mechanic nhỏ: visit 3 ngày liên tiếp = reward

### 2. Design campaign + voucher

**Bạn hỏi:**
> "Muốn reactivate lapsed users (inactive 30-60 ngày, từng order ≥3 lần). Budget khoảng 100M. Nên làm gì?"

**Claude trả lời:**
> **Campaign level M** — budget 50-200M VND, timeline 2-4 tuần. Channels: in-app push + paid social.
>
> Với lapsed segment có lịch sử order tốt:
> - **Fixed discount 40-50%**, không min spend
> - Expiry **48 giờ** — tạo urgency, không để họ "để mai"

### 3. Churn risk + điểm thưởng

**Bạn hỏi:**
> "Segment này 45 ngày chưa active, 12.000 users, trung bình còn 320 điểm chưa dùng. Nguy cơ thế nào?"

**Claude trả lời:**
> **Medium risk** — đang tiến gần ngưỡng churn. 320 điểm tích luỹ là hook tốt: nhắc điểm sắp hết hạn kết hợp offer nhỏ hiệu quả hơn discount đơn thuần.

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

---

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

---

## Tools

| Tool | Làm gì | Input chính |
|---|---|---|
| `design_campaign` | Brief campaign theo level S/M/L | level, objective, segment |
| `suggest_voucher` | Voucher phù hợp segment | segment, objective, budget_level |
| `analyze_retention` | Phân tích cohort, tìm điểm drop | cohort_data (JSON), campaign_level |
| `predict_churn_risk` | Đánh giá nguy cơ churn | days_inactive, users, points |
| `analyze_experiment` | Đọc kết quả A/B test | control/treatment counts + sample sizes |
| `estimate_sample_size` | Tính sample size trước khi test | baseline_rate, MDE |

## Giới hạn

Tool trả output dạng framework/recommendation, không kéo real data từ database. Giúp **tư duy nhanh hơn**, không thay thế data analyst.

---

---

# Growth MCP

MCP server for growth marketing — packaging domain knowledge into tools Claude can call directly in chat.

---

## What problem does it solve?

Growth PMs often spend time repeating the same analyses: calculating drop rates from cohort data, remembering which interventions fit which budget level, looking up sample size formulas, designing vouchers by segment...

**growth-mcp** packages this logic so Claude can call it directly in chat and return actionable output — not generic advice.

---

## Real examples

### 1. Retention cohort analysis

**You ask:**
> "March cohort: week_0=100%, week_1=62%, week_2=41%, week_3=28%, week_4=21%. Small budget. Analyse this for me."

**Claude responds:**
> Biggest drop at **W0→W1: 38%** — this is an early activation problem, not a retention problem. Later-stage retention (W1→W2: 33.9%, W2→W3: 31.7%) is actually quite stable.
>
> With a small budget, focus on W0→W1 first:
> - In-app push reminder within the first 24h
> - Time-based trigger: if no return after 3 days → send offer
> - Simple streak mechanic: visit 3 days in a row = reward

### 2. Campaign design + voucher

**You ask:**
> "I want to reactivate lapsed users (inactive 30-60 days, had ≥3 orders). Budget around 100M. What should I do?"

**Claude responds:**
> **Campaign level M** — budget 50-200M VND, timeline 2-4 weeks. Channels: in-app push + paid social.
>
> For a lapsed segment with a strong order history:
> - **Fixed discount 40-50%**, no min spend
> - Expiry **48 hours** — creates urgency

### 3. Churn risk + loyalty points

**You ask:**
> "This segment hasn't been active for 45 days, 12,000 users, average 320 unused points. How at risk are they?"

**Claude responds:**
> **Medium risk** — approaching the churn threshold. 320 accumulated points are a strong hook: reminding them their points are expiring combined with a small offer works better than a standalone discount.

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

---

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

---

## Tools

| Tool | What it does | Key inputs |
|---|---|---|
| `design_campaign` | Campaign brief by level S/M/L | level, objective, segment |
| `suggest_voucher` | Voucher recommendation by segment | segment, objective, budget_level |
| `analyze_retention` | Cohort analysis, find biggest drop point | cohort_data (JSON), campaign_level |
| `predict_churn_risk` | Assess churn risk level | days_inactive, users, points |
| `analyze_experiment` | Read A/B test results with stats | control/treatment counts + sample sizes |
| `estimate_sample_size` | Calculate sample size before running a test | baseline_rate, MDE |

## Limitations

Tools return framework-level output and recommendations — they don't pull real data from a database. Meant to **speed up thinking**, not replace a data analyst.

---

## License

MIT
