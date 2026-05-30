# tools/voucher.py

import json
from mcp.server import Server
from mcp.types import TextContent

MAX_PCT_DISCOUNT = 25  # hard cap thực tế market VN


def register_voucher_tools(server: Server):

    @server.tool()
    async def optimize_voucher(
        avg_order_value_vnd: int,
        target_conversion_lift_pct: float,
        budget_per_user_vnd: int,
        voucher_type: str = "fixed"
    ) -> list[TextContent]:
        """
        Thiết kế voucher ladder tối ưu với abuse risk assessment.

        Args:
            avg_order_value_vnd: AOV hiện tại tính bằng VND
            target_conversion_lift_pct: Target lift conversion %. Ví dụ 20 = muốn tăng 20%
            budget_per_user_vnd: Budget tối đa per user VND
            voucher_type: "fixed" (cashback VND) hoặc "percentage" (% giảm giá)
        """
        if voucher_type == "percentage":
            base = min(target_conversion_lift_pct * 0.6, MAX_PCT_DISCOUNT * 0.6)
            tiers = [
                {"spend_threshold": int(avg_order_value_vnd * 0.8),
                 "discount": f"{base:.0f}%"},
                {"spend_threshold": int(avg_order_value_vnd * 1.0),
                 "discount": f"{min(base * 1.4, MAX_PCT_DISCOUNT):.0f}%"},
                {"spend_threshold": int(avg_order_value_vnd * 1.5),
                 "discount": f"{min(base * 1.7, MAX_PCT_DISCOUNT):.0f}%"},
            ]
        else:
            # Fixed: step từ budget, tăng đều để giữ incentive ở mỗi tier
            step = int(budget_per_user_vnd * 0.5)
            tiers = [
                {"spend_threshold": int(avg_order_value_vnd * 0.8),
                 "discount": f"{step:,} VND"},
                {"spend_threshold": int(avg_order_value_vnd * 1.0),
                 "discount": f"{step * 2:,} VND"},
                {"spend_threshold": int(avg_order_value_vnd * 1.5),
                 "discount": f"{step * 3:,} VND"},
            ]

        ratio = budget_per_user_vnd / avg_order_value_vnd
        abuse_risk = "HIGH" if ratio > 0.15 else "MEDIUM" if ratio > 0.08 else "LOW"

        result = {
            "voucher_ladder": tiers,
            "abuse_risk": abuse_risk,
            "abuse_flags": [
                "Cần limit 1 voucher/user/device",
                "Verify phone trước khi phát" if abuse_risk != "LOW"
                else "Risk thấp - standard guardrails đủ",
            ],
            "estimated_cost_per_conversion": f"{int(budget_per_user_vnd):,} VND",
        }

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
