"""
daily_report
รายงานยอดขายประจำวัน - KKBalloon
อ่านข้อมูลจาก orders.csv และแสดงสรุปยอดขายเป็นภาษาไทย

รูปแบบ CSV ที่รองรับ:
  date, customer_name, item, quantity, price_per_unit, status, channel
  วันที่รูปแบบ DD/MM/YYYY หรือ YYYY-MM-DD ก็ได้
"""

import csv
import os
import sys
from datetime import date, datetime
from collections import defaultdict, Counter

# ─────────────────────────────────────────
# CONFIG — ชื่อคอลัมน์ใน CSV
# ─────────────────────────────────────────
CSV_FILE      = "orders.csv"
COL_DATE      = "date"
COL_PRODUCT   = "item"
COL_QTY       = "quantity"
COL_PRICE     = "price_per_unit"
COL_STATUS    = "status"
COL_CHANNEL   = "channel"


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def parse_date(s: str) -> str:
    """แปลงวันที่ DD/MM/YYYY หรือ YYYY-MM-DD → YYYY-MM-DD"""
    s = s.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s  # คืนค่าเดิมถ้าแปลงไม่ได้


def fmt_baht(amount: float) -> str:
    return f"฿{amount:,.2f}"


def bar(count: int, total: int, width: int = 18) -> str:
    filled = round(count / total * width) if total else 0
    return "█" * filled + "░" * (width - filled)


def load_orders(filepath: str, target_date: str) -> list[dict]:
    """โหลดออเดอร์จาก CSV กรองเฉพาะวันที่ระบุ"""
    if not os.path.exists(filepath):
        print(f"⚠️  ไม่พบไฟล์ {filepath!r}")
        print("   วางไฟล์ orders.csv ไว้ในโฟลเดอร์เดียวกับสคริปต์นี้\n")
        sys.exit(1)

    orders = []
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if parse_date(row.get(COL_DATE, "")) == target_date:
                orders.append(row)
    return orders


def load_all_orders(filepath: str) -> list[dict]:
    """โหลดออเดอร์ทั้งหมดในไฟล์ (ใช้สำหรับ --all)"""
    if not os.path.exists(filepath):
        print(f"⚠️  ไม่พบไฟล์ {filepath!r}")
        sys.exit(1)
    orders = []
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            orders.append(row)
    return orders


# ─────────────────────────────────────────
# REPORT
# ─────────────────────────────────────────
def print_report(orders: list[dict], label: str) -> None:
    LINE  = "═" * 50
    LINE2 = "─" * 50

    # ── คำนวณ ──────────────────────────────────────
    total_revenue  = 0.0
    paid_revenue   = 0.0
    paid_count     = 0
    pending_count  = 0
    product_qty    = defaultdict(int)
    product_rev    = defaultdict(float)
    channel_count  = Counter()

    for o in orders:
        try:
            qty   = int(o.get(COL_QTY,   0))
            price = float(o.get(COL_PRICE, 0))
        except ValueError:
            continue
        status  = o.get(COL_STATUS,  "").strip().lower()
        channel = o.get(COL_CHANNEL, "ไม่ระบุ").strip()
        product = o.get(COL_PRODUCT, "ไม่ระบุ").strip()
        rev     = qty * price

        total_revenue      += rev
        product_qty[product] += qty
        product_rev[product] += rev
        channel_count[channel] += 1

        if status == "paid":
            paid_revenue += rev
            paid_count   += 1
        else:
            pending_count += 1

    total_orders   = len(orders)
    pending_revenue = total_revenue - paid_revenue
    top3 = sorted(product_qty.items(), key=lambda x: x[1], reverse=True)[:3]

    # ── พิมพ์ ───────────────────────────────────────
    print()
    print(LINE)
    print(f"  🎈  รายงานยอดขายประจำวัน — KKBalloon")
    print(f"  📅  {label}")
    print(LINE)

    # 1. ยอดขายรวม
    print(f"\n  💰  ยอดขายรวม")
    print(LINE2)
    print(f"  {'รวมทั้งหมด':<22} {fmt_baht(total_revenue):>12}")
    print(f"  {'✅ ชำระแล้ว (paid)':<22} {fmt_baht(paid_revenue):>12}")
    print(f"  {'⏳ รอชำระ (pending)':<22} {fmt_baht(pending_revenue):>12}")

    # 2. จำนวนออเดอร์
    print(f"\n  📋  จำนวนออเดอร์ทั้งหมด : {total_orders} รายการ")
    print(LINE2)

    # 3. สถานะ
    if total_orders:
        print(f"  ✅ paid     {bar(paid_count,    total_orders)}  {paid_count} รายการ")
        print(f"  ⏳ pending  {bar(pending_count, total_orders)}  {pending_count} รายการ")

    # 4. สินค้าขายดี Top 3
    print(f"\n  🏆  สินค้าขายดี 3 อันดับ")
    print(LINE2)
    medals = ["🥇", "🥈", "🥉"]
    for rank, (prod, qty) in enumerate(top3):
        print(f"  {medals[rank]}  {prod}")
        print(f"      จำนวน {qty} ชิ้น   รายได้ {fmt_baht(product_rev[prod])}")

    # 5. ช่องทาง
    print(f"\n  📣  ช่องทางที่ได้รับออเดอร์")
    print(LINE2)
    top_ch = channel_count.most_common(1)[0][0] if channel_count else ""
    for ch, cnt in channel_count.most_common():
        icon  = "🚶" if ch == "walk-in" else "📲"
        star  = "  ⭐ อันดับ 1" if ch == top_ch else ""
        print(f"  {icon} {ch:<12} {bar(cnt, total_orders, 15)}  {cnt} รายการ{star}")

    print()
    print(LINE)
    print(f"  📊 สรุป: {total_orders} ออเดอร์  |  รายได้รวม {fmt_baht(total_revenue)}")
    print(LINE)
    print()


# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────
if __name__ == "__main__":
    # วิธีใช้:
    #   python daily_report.py                  → วันนี้
    #   python daily_report.py 2025-05-09       → วันที่ระบุ (YYYY-MM-DD)
    #   python daily_report.py --all            → ทุกออเดอร์ในไฟล์

    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        orders = load_all_orders(CSV_FILE)
        label  = f"สรุปทั้งหมด ({len(orders)} รายการ)"
    else:
        target = sys.argv[1] if len(sys.argv) > 1 else str(date.today())
        # รองรับ DD/MM/YYYY จาก argument ด้วย
        target = parse_date(target)
        orders = load_orders(CSV_FILE, target)
        label  = f"วันที่ {target}"

    if not orders:
        print(f"\n⚠️  ไม่พบออเดอร์สำหรับ: {label}")
        print(f"   ตรวจสอบวันที่ในไฟล์ หรือลอง: python daily_report.py --all\n")
    else:
        print_report(orders, label)
