# Growth MCP

MCP server cho growth marketing — đóng gói domain knowledge thành tools Claude có thể gọi trực tiếp trong chat.

Built từ kinh nghiệm thực tế tại MoMo (40M+ users).

---

## Giải quyết vấn đề gì?

Growth PM thường mất thời gian làm đi làm lại các phân tích lặp: tính drop rate từ cohort data, nhớ intervention nào phù hợp budget nào, tra công thức sample size, design voucher theo segment... Mỗi việc nhỏ nhưng cộng lại tốn cả buổi.

**growth-mcp** đóng gói những logic này lại. Claude gọi trực tiếp trong chat, trả kết quả có thể dùng ngay — không còn trả lời chung chung.

---

## Minh hoạ thực tế

### 1. Phân tích retention cohort

**Bạn hỏi:**
> "Cohort tháng 3 của tôi: week_0=100%, week_1=62%, week_2=41%, week_3=28%, week_4=21%. Budget nhỏ thôi. Phân tích giúp tôi."

**Claude gọi** `analyze_retention` rồi trả lời:

> Drop lớn nhất ở **W0→W1: 38%** — đây là early activation problem, không phải retention problem. Retention về sau (W1→W2: 33.9%, W2→W3: 31.7%) thực ra khá ổn định.
>
> Với budget S, nên tập trung vào W0→W1 trước:
> - In-app push reminder trong 24h đầu
> - Time-based trigger: nếu chưa quay lại sau 3 ngày → send offer
> - Streak mechanic nhỏ: visit 3 ngày liên tiếp = reward

---

### 2. Design campaign + voucher

**Bạn hỏi:**
> "Tôi muốn reactivate lapsed users (inactive 30-60 ngày, từng order ≥3 lần). Budget khoảng 100M. Nên làm gì?"

**Claude gọi** `design_campaign` + `suggest_voucher` rồi trả lời:

> **Campaign level M** — budget 50-200M VND, timeline 2-4 tuần.
> Channels: in-app push, in-app banner, owned out-app + paid social/search.
>
> Với lapsed segment có lịch sử order tốt, nên dùng:
> - **Fixed discount 40-50%**, không min spend (barrier thấp để quay lại)
> - Expiry **48 giờ** — tạo urgency, không để họ "để mai"
> - Primary channel: in-app push (họ vẫn còn app, chỉ chưa mở)

---

### 3. Churn risk + điểm thưởng

**Bạn hỏi:**
> "Segment này 45 ngày chưa active, 12.000 users, trung bình còn 320 điểm chưa dùng. Nguy cơ churn thế nào?"

**Claude gọi** `predict_churn_risk` rồi trả lời:

> **Medium risk** — đang tiến gần ngưỡng churn (>60 ngày = high risk).
>
> 320 điểm tích luỹ là hook tốt: nhắc họ điểm sắp hết hạn kết hợp offer nhỏ hiệu quả hơn discount đơn thuần.
> Channel: in-app push + SMS/email. Urgency: medium.

---

### 4. Đọc kết quả A/B test

**Bạn hỏi:**
> "A/B test checkout flow: control 847 convert / 10.000 users, treatment 923 / 10.000. Có nên launch không?"

**Claude gọi** `analyze_experiment` rồi trả lời:

> Control: **8.47%** → Treatment: **9.23%** (+8.97% relative lift)
>
> z = 1.89, **p = 0.058** → **chưa significant** (threshold 0.05).
>
> Chưa nên launch. Cần thêm ~2-3 tuần data hoặc tăng traffic. Nếu launch sớm, 6% chance đây là noise.
> Gợi ý: segment theo new vs returning users — lift có thể đến từ một nhóm cụ thể.

---

### 5. Tính sample size trước khi chạy test

**Bạn hỏi:**
> "Conversion rate hiện tại 3.2%, muốn detect được lift 15%. Cần bao nhiêu users?"

**Claude gọi** `estimate_sample_size` rồi trả lời:

> Cần **30.307 users/variant**, tổng **60.614 users** (power 90%, α=5%).
>
> Với traffic hiện tại, ước tính cần khoảng X tuần để đủ sample — nên plan trước, không chạy rồi mới tính.

---

## Cài đặt

```bash
git clone https://github.com/thaolst/growth-mcp.git
cd growth-mcp
pip install -e .
```

## Dùng với Claude Desktop

Thêm vào `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) hoặc `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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

Thêm vào `.cursor/mcp.json` trong project:

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

## License

MIT
