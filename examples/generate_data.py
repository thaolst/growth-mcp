"""Generate the synthetic sample datasets in this folder.

All sample data is synthetic, generated with a fixed seed for
reproducibility. Numbers are shaped to look like a realistic loyalty
program but correspond to no real product or company.
"""

import csv
import random

random.seed(42)


def ab_test_raw(path="ab_test_raw.csv", n_per_group=2500):
    """1 row per user: treatment gets a slightly better conversion rate."""
    rates = {"control": 0.082, "treatment": 0.097}
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "group", "converted"])
        uid = 0
        for group, rate in rates.items():
            for _ in range(n_per_group):
                uid += 1
                w.writerow([f"u{uid:05d}", group, 1 if random.random() < rate else 0])


def retention_weekly(path="retention_weekly.csv"):
    """Active user counts per week for one cohort, with a plateau."""
    counts = [10000, 5800, 4300, 3600, 3200, 2950, 2820, 2760, 2730]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["period", "active_users"])
        for i, n in enumerate(counts):
            w.writerow([f"week_{i}", n])


def segment_balances(path="segment_balances.csv", n=3000):
    """1 row per user: segment and points balance."""
    profiles = {
        "new": (0.4, 80, 60),        # share, mean, sd
        "active": (0.35, 950, 400),
        "power": (0.1, 3200, 900),
        "lapsed": (0.15, 420, 300),
    }
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "segment", "points_balance"])
        uid = 0
        for seg, (share, mean, sd) in profiles.items():
            for _ in range(int(n * share)):
                uid += 1
                bal = max(0, int(random.gauss(mean, sd)))
                w.writerow([f"u{uid:05d}", seg, bal])


def redemption_price_periods(path="redemption_price_periods.csv"):
    """Redemption volume per segment across 4 price periods.

    Shaped so the 'new' segment is clearly price sensitive and the
    'power' segment barely reacts.
    """
    periods = ["2026-02", "2026-03", "2026-04", "2026-05"]
    prices = [100, 80, 100, 70]
    base = {"new": 1200, "active": 2600, "power": 900}
    sensitivity = {"new": 1.9, "active": 0.9, "power": 0.2}
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["period", "segment", "points_price", "redemptions"])
        for period, price in zip(periods, prices):
            for seg, q0 in base.items():
                # đơn giản: lượng tăng khi giá giảm, theo độ nhạy của segment
                q = q0 * (100 / price) ** sensitivity[seg]
                q *= random.uniform(0.97, 1.03)
                w.writerow([period, seg, price, int(q)])


if __name__ == "__main__":
    ab_test_raw()
    retention_weekly()
    segment_balances()
    redemption_price_periods()
    print("generated 4 sample datasets")
