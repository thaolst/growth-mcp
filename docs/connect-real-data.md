# Ket noi data that vao growth-mcp

Ba lop data duoc ho tro: CSV (nhanh nhat, chay ngay), BigQuery (cho data warehouse), Mixpanel (cho event stream). Trang nay giai thich cach noi tung lop voi cac truong hop dung thuc te trong fintech/e-commerce SEA.

## Chon lop data nao?

| Truong hop | Lop nen dung |
|---|---|
| Export nhanh tu dashboard, chay phan tich mot lan | CSV |
| Data warehouse cua cong ty, can ket qua tu dong hoac lap lai | BigQuery |
| Phan tich hanh vi user theo event (click, transaction, voucher dung) | Mixpanel |
| Khong co API, chi co file Excel/CSV tu BO | CSV (convert truoc) |

## Lop 1: CSV

Nhanh nhat. Khong can config, khong can token.

### Tien xu ly

```bash
# Kiem tra file truoc khi dua vao tool
# Yeu cau: UTF-8, co header row, khong co hang trong dau file
file -I data.csv
head -3 data.csv
```

Export tu cac he thong thuong gap:

**Tableau / Metabase / Redash**: File → Export CSV. Chon "Current view" de lay dung columns dang hien thi, khong lay toan bo bang.

**BigQuery console**: sau khi chay query → Save results → CSV (local file). Nhanh hon dung tool BigQuery truc tiep neu chi can chay 1 lan.

**Mixpanel**: People → Segmentation → Export. Chon event va thoi gian roi export.

### Workflow A/B test tu export

File co dang: 1 row/user, co cot group (control/treatment), cot conversion (0/1 hoac true/false).

```
user_id,group,converted,segment
u001,control,1,new
u002,treatment,0,active
u003,treatment,1,lapsed
...
```

Cach dung voi Claude:

```
Doc file ab_test_june.csv roi phan tich A/B test. Cot group la "group", cot conversion la "converted". Kiem tra ca theo tung segment.
```

Claude goi `inspect_csv` de xem cau truc truoc, sau do `analyze_experiment_from_csv`.

### Workflow retention tu data xu (loyalty points)

File tu dashboard xu, co dang: 1 row/tuan, cot active users.

```
week,active_users
week_0,15420
week_1,9102
week_2,6341
week_3,4890
week_4,4215
```

Tool tu dong normalize (chia cho week_0) neu value lon hon 1.

```
Phan tich retention tu file cohort_xu_q2.csv, cot period la "week", cot value la "active_users". Campaign level M.
```

### Workflow elasticity gia doi xu

File tu lich su promotion, moi dong la 1 period-segment:

```
period,price_point,redemptions,segment
2025-Q1,100,8420,new
2025-Q1,100,12300,active
2025-Q2,80,11200,new
2025-Q2,80,13100,active
2025-Q3,120,6800,new
...
```

```
Phan tich price elasticity theo segment tu file xu_elasticity_2025.csv
```

Output phan loai tung segment: HIGHLY_ELASTIC / MODERATELY_INELASTIC / INELASTIC. Dung de quyet dinh segment nao duoc chay promotion gia diem, segment nao khong can.

## Lop 2: BigQuery

Dung khi data o warehouse va can ket qua tu dong hoac lap lai theo lich.

### Cai dat

```bash
pip install "growth-mcp[bigquery]"

# Auth: chon 1 trong 2
gcloud auth application-default login
# hoac
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

Service account can quyen: BigQuery Data Viewer + BigQuery Job User. Khong can quyen write.

### A/B test tu bang warehouse

```sql
-- Vi du: bang event tu data pipeline
SELECT
  user_id,
  experiment_group AS group,
  CAST(did_convert AS INT64) AS converted
FROM `project.analytics.ab_assignments`
WHERE experiment_name = 'voucher_new_users_jun2025'
  AND event_date BETWEEN '2025-06-01' AND '2025-06-30'
```

Cach dung voi Claude:

```
Dung BigQuery phan tich A/B test sau voi SQL nay: [dan SQL]. Project la "momo-analytics". Cot group la "group", cot conversion la "converted".
```

Guardrail: chi cho phep SELECT/WITH, tu choi tat ca cac query write. Row limit 200K - neu bang lon hon, aggregate trong SQL truoc.

### Retention cohort tu event stream

```sql
SELECT
  CONCAT('week_', CAST(week_num AS STRING)) AS period,
  COUNT(DISTINCT user_id) AS active_users
FROM (
  SELECT
    user_id,
    DATE_DIFF(event_date, cohort_start, WEEK) AS week_num
  FROM `project.analytics.xu_redemptions` r
  JOIN `project.analytics.user_cohorts` c USING (user_id)
  WHERE r.event_date >= c.cohort_start
    AND DATE_DIFF(r.event_date, c.cohort_start, WEEK) <= 8
)
GROUP BY week_num
ORDER BY week_num
```

### Segment stats tu bang balance

```sql
SELECT
  segment_type AS segment,
  xu_balance AS balance
FROM `project.xu.user_balances_snapshot`
WHERE snapshot_date = CURRENT_DATE()
  AND xu_balance > 0
```

Phan tich phan phoi balance theo segment, tim segment nao dang giu nhieu xu nhat va co nguy co dormancy cao nhat.

## Lop 3: Mixpanel

Dung khi can phan tich hanh vi theo event (click, open, transaction, voucher_redeemed).

### Cai dat

```bash
# Lay API secret: Mixpanel → Project Settings → Project Secret
export MIXPANEL_API_SECRET=your_project_api_secret

# EU data residency (neu project o EU)
export MIXPANEL_API_HOST=data-eu.mixpanel.com
```

Khong can cai them package. Dung stdlib urllib.

### A/B test tu exposure + conversion event

```
Phan tich A/B test tu Mixpanel: exposure event la "experiment_viewed", conversion event la "transaction_completed". Property phan nhom la "experiment_group". Tu 2025-06-01 den 2025-06-30.
```

Tool lay exposure event (user nao duoc assign vao group nao) va conversion event (user nao convert), join theo distinct_id, chay z-test.

Gioi han: 90 ngay, 200K events. Neu lon hon, dung date range ngan hon hoac export ra CSV truoc.

### Segment stats tu event property

```
Tom tat xu redemptions theo segment tu Mixpanel. Event la "xu_redeemed", segment property la "user_segment", value property la "xu_amount". Tu 2025-06-01 den 2025-06-30.
```

## Pattern thuc te: tu raw data den quyet dinh

Workflow thong thuong trong 1 campaign cycle:

**1. Doc data**

```
Inspect file segment_balances_jun.csv de xem cau truc
```

**2. Hieu trang thai**

```
Summarize xu_balance theo segment trong file nay. Segment col la "user_segment", value col la "xu_balance"
```

**3. Du bao can thiep**

```
Segment "lapsed" co 45 ngay chua active, trung binh 380 xu. Danh gia churn risk va de xuat voucher phu hop.
```

**4. Design campaign**

```
Design campaign reactivation cho lapsed segment, budget level M, objective la "retention"
```

**5. Sau campaign: doc ket qua**

```
Phan tich A/B test tu file ab_results_reactivation.csv: cot group la "variant", cot conversion la "transacted"
```

Toan bo 5 buoc nay chay trong 1 Claude chat session. Khong can switch tool, khong can viet code.

## Xu ly loi thuong gap

**CSV: "Column not found"**

```
Inspect file truoc: "inspect_csv /path/to/file.csv"
Tool tra ve dung ten cot de paste vao query tiep theo.
```

**BigQuery: "BigQuery query failed: 403"**

Service account thieu quyen. Kiem tra: BigQuery Data Viewer (de doc data) va BigQuery Job User (de chay query).

**BigQuery: "Query returned no rows"**

Chay query trong BigQuery console truoc de xac nhan co data. Filter WHERE co the qua chat.

**Mixpanel: "MIXPANEL_API_SECRET is not set"**

```bash
echo $MIXPANEL_API_SECRET  # kiem tra env var da duoc set chua
```

Neu dung Claude Desktop, khoi dong lai sau khi export env var.

**Mixpanel: "Date range capped at 90 days"**

Chia nho khoang thoi gian hoac export ra CSV truoc.

## Gioi han va luu y

- CSV: gioi han 50 MB, encode UTF-8 (dung UTF-8 with BOM neu export tu Excel)
- BigQuery: chi SELECT/WITH, toi da 200K rows, nen aggregate trong SQL neu data lon
- Mixpanel: toi da 90 ngay, 200K events, lay distinct_id lam user key
- Tat ca cac tool doc-only: khong ghi, khong thay doi data goc

Neu nguon data khac (Amplitude, Segment, Clevertap, noi bo): export ra CSV truoc, sau do dung CSV layer.
