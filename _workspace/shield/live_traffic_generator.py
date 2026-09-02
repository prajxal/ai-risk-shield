"""
Synthetic Live Traffic Generator for Return-Risk Shield (AI Risk Manager - Track 02).
Produces realistic e-commerce order/return events mixing legitimate returns (~60%)
and return-abuse attacks (~40%: Wardrobing, Bracketing Abuse, Serial-Returner Fraud, False Damage Claims).
Guarantees strict Customer & Event ID isolation (cust_live_*, ret_live_*) from demo and evaluation partitions.
"""
import random
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../requirements")))
from contracts import (
    ReturnEvent,
    CustomerProfile,
    OrderDetails,
    OrderItem,
    ReturnRequest,
    GroundTruth,
    AbuseClass,
    DecisionAction,
    ItemCategory,
)


class LiveTrafficGenerator:
    def __init__(self):
        self._counter = 0

        # -------------------------------------------------------------
        # 1. Legitimate Return Templates (~60%)
        # -------------------------------------------------------------
        self.legit_templates = [
            ("Ergonomic Vertical Optical Mouse", "ACCESSORIES", 2750, 4, "SIZE_FIT_ISSUE", "Grip slightly small for hand size", "TAGS_ATTACHED", "Standard legitimate accessory return."),
            ("USB Podcast Cardioid Microphone", "ELECTRONICS", 6499, 5, "DID_NOT_LIKE", "Acoustic profile too sensitive for unpadded room", "TAGS_ATTACHED", "Standard audio equipment return on clean profile."),
            ("Dual Heavy-Duty Desk Monitor Mount", "HOME_APPLIANCES", 4499, 3, "SIZE_FIT_ISSUE", "Clamp does not fit desk crossbar", "TAGS_ATTACHED", "Legitimate hardware fit issue."),
            ("Pastel Sticky Note Memo Cubes (12-Pack)", "ACCESSORIES", 1050, 2, "WRONG_ITEM_SENT", "Received neon colors instead of pastel", "UNOPENED", "Merchant fulfillment mismatch."),
            ("Smart Wi-Fi Dimmable LED Desk Lamp", "HOME_APPLIANCES", 2999, 4, "DID_NOT_LIKE", "Color temperature does not go warm enough", "TAGS_ATTACHED", "Aesthetic preference return on clean account."),
            ("Hi-Fi Dual Dynamic In-Ear Earphones", "ELECTRONICS", 1850, 3, "DEFECTIVE_DAMAGED", "Left earbud has static hum", "TAGS_ATTACHED", "Genuine defect claim on low-cost item."),
            ("Under Desk Steel Cable Tray Rack", "HOME_APPLIANCES", 1499, 2, "SIZE_FIT_ISSUE", "Crossbar blocks bracket mounting", "TAGS_ATTACHED", "Legitimate workspace organizer return."),
            ("Wireless Presentation Clicker with Red Laser", "ACCESSORIES", 1299, 3, "DID_NOT_LIKE", "Laser pointer button placement awkward", "TAGS_ATTACHED", "Business tool return."),
            ("24-Inch Widescreen Privacy Filter Screen", "ACCESSORIES", 2399, 4, "SIZE_FIT_ISSUE", "Does not fit curved monitor bezel", "TAGS_ATTACHED", "Legitimate accessory sizing issue."),
            ("65W GaN Dual Port USB-C Wall Charger", "ELECTRONICS", 3199, 5, "DEFECTIVE_DAMAGED", "Port 2 does not negotiate fast charge", "TAGS_ATTACHED", "Clean hardware defect return."),
            ("Magnetic Dry Erase Whiteboard 60x45cm", "HOME_APPLIANCES", 1390, 2, "DEFECTIVE_DAMAGED", "Frame corner bent during courier transit", "TAGS_ATTACHED", "Transit damage on fragile item."),
            ("Ergonomic Gel Wrist Rest Mousepad", "ACCESSORIES", 850, 3, "DID_NOT_LIKE", "Gel rest is too firm", "TAGS_ATTACHED", "Standard accessory return."),
            ("Cotton Casual Polo Shirt (Navy)", "FAST_FASHION", 1299, 3, "SIZE_FIT_ISSUE", "Shoulder seam is narrow", "TAGS_ATTACHED", "Standard apparel size issue."),
            ("Stainless Steel Double Wall Flask 1L", "HOME_APPLIANCES", 899, 4, "DID_NOT_LIKE", "Larger than expected for daily commute", "TAGS_ATTACHED", "Clean preference return."),
            ("Wireless Silent Mechanical Keyboard", "ELECTRONICS", 4800, 5, "DEFECTIVE_DAMAGED", "Bluetooth key lag on macOS", "TAGS_ATTACHED", "Software compatibility issue return.")
        ]

        # -------------------------------------------------------------
        # 2. Wardrobing Templates (~12%)
        # -------------------------------------------------------------
        self.wardrobe_templates = [
            ("Embroidered Raw Silk Festive Lehenga", "APPAREL_LUXURY", 32000, 28, "DID_NOT_LIKE", "Wedding reception completed, color slightly bright", "TAGS_REMOVED", "High-confidence Wardrobing: luxury occasionwear returned at day 28 with tags removed.", DecisionAction.BLOCK),
            ("Bespoke Italian Tuxedo Suit", "APPAREL_LUXURY", 24000, 26, "DID_NOT_LIKE", "Awards gala finished, fit felt tight", "USED_ONCE", "Wardrobing: luxury tuxedo used for awards function and returned on day 26.", DecisionAction.BLOCK),
            ("Handcrafted Kanjeevaram Silk Saree", "APPAREL_LUXURY", 19500, 24, "DID_NOT_LIKE", "Worn to family wedding ceremony", "USED_ONCE", "Wardrobing flag: luxury saree worn to family event.", DecisionAction.FLAG),
            ("Designer Velvet Anarkali Suit", "APPAREL_LUXURY", 14500, 22, "DID_NOT_LIKE", "Sangeet ceremony over", "USED_ONCE", "Wardrobing flag: festive occasionwear returned after event.", DecisionAction.FLAG),
        ]

        # -------------------------------------------------------------
        # 3. Bracketing Templates (~12%)
        # -------------------------------------------------------------
        self.bracket_templates = [
            ("Italian Leather Derby Shoes", "FOOTWEAR", 7800, [("SKU_DRB_41", "Size 41", "41", "Black"), ("SKU_DRB_42", "Size 42", "42", "Black"), ("SKU_DRB_43", "Size 43", "43", "Black")], 2, "Bracketing: ordered 3 sizes of luxury footwear and returning 2.", DecisionAction.FLAG),
            ("Tailored Linen Summer Blazer", "APPAREL_LUXURY", 11500, [("SKU_BLZ_38", "Size 38", "38", "Beige"), ("SKU_BLZ_40", "Size 40", "40", "Beige"), ("SKU_BLZ_42", "Size 42", "42", "Beige")], 3, "Severe bracketing: ordered 3 sizes of luxury blazer and returning all 3.", DecisionAction.BLOCK),
            ("Merino Wool Knit Sweater", "FAST_FASHION", 3800, [("SKU_SWT_M", "Size M", "M", "Navy"), ("SKU_SWT_L", "Size L", "L", "Navy")], 1, "Size bracketing on knit sweaters.", DecisionAction.FLAG),
            ("Premium Chelsea Boots", "FOOTWEAR", 6200, [("SKU_CH_BLK", "Black Pair", "42", "Black"), ("SKU_CH_BRN", "Brown Pair", "42", "Brown")], 1, "Color bracketing: bought black and brown pair, returning one.", DecisionAction.FLAG),
        ]

        # -------------------------------------------------------------
        # 4. Serial Returner Fraud Templates (~8%)
        # -------------------------------------------------------------
        self.serial_templates = [
            ("Pro Streaming USB Microphone", "ELECTRONICS", 7500, 10, 8, 0.80, 2, "Serial returner: 80% return rate + 2 prior chargebacks.", DecisionAction.BLOCK),
            ("Studio Reference Monitor Speakers", "ELECTRONICS", 18500, 8, 7, 0.875, 1, "Chronic serial returner: 87.5% return rate + prior dispute.", DecisionAction.BLOCK),
            ("4K Ultra-Wide Curved Gaming Monitor", "ELECTRONICS", 32000, 14, 11, 0.786, 0, "High velocity serial returner on high-ticket monitors.", DecisionAction.BLOCK),
            ("RGB Mechanical Gaming Keyboard", "ELECTRONICS", 5800, 9, 5, 0.556, 0, "Elevated return velocity (55.6%) on electronics.", DecisionAction.FLAG),
        ]

        # -------------------------------------------------------------
        # 5. False Damage Claims Templates (~8%)
        # -------------------------------------------------------------
        self.damage_templates = [
            ("Flagship Smartwatch Cellular 49mm", "ELECTRONICS", 45000, 10, "COD", "INSTANT_CASH", "MISSING_PARTS", "False damage claim on ₹45k smartwatch on COD requesting instant cash refund.", DecisionAction.BLOCK),
            ("Ultra Fast NVMe Portable SSD 2TB", "ELECTRONICS", 16900, 15, "COD", "INSTANT_CASH", "MISSING_PARTS", "Empty box / component swap risk on portable SSD on COD.", DecisionAction.BLOCK),
            ("Compact Action Camera 4K60 Kit", "ELECTRONICS", 22500, 120, "UPI", "ORIGINAL_PAYMENT_METHOD", "TAGS_ATTACHED", "High-ticket action camera damage claim requiring inspection.", DecisionAction.FLAG),
        ]

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def generate_transaction(self, attack_ratio: float = 0.4) -> ReturnEvent:
        """
        Generates a synthetic ReturnEvent with isolated namespace (`cust_live_*`, `ret_live_*`).
        """
        self._counter += 1
        now_ts = self._now_iso()
        event_id = f"ret_live_{uuid.uuid4().hex[:8]}"
        is_attack = random.random() < attack_ratio

        if not is_attack:
            # Generate Legitimate Return
            t = random.choice(self.legit_templates)
            title, cat, price, days, code, notes, cond, rationale = t
            cust_id = f"cust_live_legit_{uuid.uuid4().hex[:6]}"
            item = OrderItem(sku=f"SKU_LIVE_{uuid.uuid4().hex[:6]}", title=title, category=cat, unit_price=price)
            
            return ReturnEvent(
                event_id=event_id,
                is_synthetic=True,
                split="live",
                timestamp=now_ts,
                customer_profile=CustomerProfile(
                    customer_id=cust_id,
                    account_age_days=random.randint(90, 600),
                    total_orders_count=random.randint(6, 30),
                    total_returns_count=random.randint(0, 3),
                    historical_return_rate=round(random.uniform(0.05, 0.18), 3),
                    past_return_reasons=["SIZE_FIT_ISSUE"],
                    dispute_chargeback_count=0
                ),
                order_details=OrderDetails(
                    order_id=f"ord_live_{uuid.uuid4().hex[:6]}",
                    order_date=now_ts,
                    days_since_purchase=days,
                    total_order_amount=price,
                    currency="INR",
                    payment_method="UPI",
                    items=[item]
                ),
                return_request=ReturnRequest(
                    return_id=f"req_live_{uuid.uuid4().hex[:6]}",
                    return_reason_code=code,
                    return_reason_notes=notes,
                    returned_items=[item],
                    requested_refund_amount=price,
                    refund_destination="ORIGINAL_PAYMENT_METHOD",
                    item_condition_tag=cond
                ),
                ground_truth=GroundTruth(
                    target_abuse_class=AbuseClass.BENIGN,
                    expected_decision=DecisionAction.ALLOW,
                    failure_case=False,
                    rationale=rationale
                )
            )

        # Generate Return Abuse Event
        abuse_kind = random.choices(["wardrobing", "bracketing", "serial", "damage"], weights=[30, 30, 20, 20])[0]

        if abuse_kind == "wardrobing":
            t = random.choice(self.wardrobe_templates)
            title, cat, price, days, code, notes, cond, rationale, dec = t
            cust_id = f"cust_live_ward_{uuid.uuid4().hex[:6]}"
            item = OrderItem(sku=f"SKU_LIVE_W_{uuid.uuid4().hex[:6]}", title=title, category=cat, unit_price=price)
            return ReturnEvent(
                event_id=event_id,
                is_synthetic=True,
                split="live",
                timestamp=now_ts,
                customer_profile=CustomerProfile(
                    customer_id=cust_id,
                    account_age_days=random.randint(60, 200),
                    total_orders_count=random.randint(2, 6),
                    total_returns_count=random.randint(1, 3),
                    historical_return_rate=round(random.uniform(0.35, 0.65), 3),
                    past_return_reasons=["DID_NOT_LIKE"],
                    dispute_chargeback_count=0
                ),
                order_details=OrderDetails(
                    order_id=f"ord_live_w_{uuid.uuid4().hex[:6]}",
                    order_date=now_ts,
                    days_since_purchase=days,
                    total_order_amount=price,
                    currency="INR",
                    payment_method="CREDIT_CARD",
                    items=[item]
                ),
                return_request=ReturnRequest(
                    return_id=f"req_live_w_{uuid.uuid4().hex[:6]}",
                    return_reason_code=code,
                    return_reason_notes=notes,
                    returned_items=[item],
                    requested_refund_amount=price,
                    refund_destination="ORIGINAL_PAYMENT_METHOD",
                    item_condition_tag=cond
                ),
                ground_truth=GroundTruth(
                    target_abuse_class=AbuseClass.WARDROBING,
                    expected_decision=dec,
                    failure_case=False,
                    rationale=rationale
                )
            )

        elif abuse_kind == "bracketing":
            t = random.choice(self.bracket_templates)
            title, cat, price, variants, ret_count, rationale, dec = t
            cust_id = f"cust_live_brk_{uuid.uuid4().hex[:6]}"
            order_items = [OrderItem(sku=f"SKU_LIVE_B_{uuid.uuid4().hex[:6]}", title=f"{title} - {v[1]}", category=cat, unit_price=price, size_variant=v[2], color_variant=v[3]) for v in variants]
            ret_items = order_items[:ret_count]
            return ReturnEvent(
                event_id=event_id,
                is_synthetic=True,
                split="live",
                timestamp=now_ts,
                customer_profile=CustomerProfile(
                    customer_id=cust_id,
                    account_age_days=random.randint(90, 250),
                    total_orders_count=random.randint(3, 8),
                    total_returns_count=random.randint(2, 5),
                    historical_return_rate=round(random.uniform(0.50, 0.75), 3),
                    past_return_reasons=["SIZE_FIT_ISSUE"],
                    dispute_chargeback_count=0
                ),
                order_details=OrderDetails(
                    order_id=f"ord_live_b_{uuid.uuid4().hex[:6]}",
                    order_date=now_ts,
                    days_since_purchase=3,
                    total_order_amount=price * len(order_items),
                    currency="INR",
                    payment_method="UPI",
                    items=order_items
                ),
                return_request=ReturnRequest(
                    return_id=f"req_live_b_{uuid.uuid4().hex[:6]}",
                    return_reason_code="SIZE_FIT_ISSUE",
                    return_reason_notes=f"Bracketed sizing: returning {ret_count} variants.",
                    returned_items=ret_items,
                    requested_refund_amount=price * ret_count,
                    refund_destination="ORIGINAL_PAYMENT_METHOD",
                    item_condition_tag="TAGS_ATTACHED"
                ),
                ground_truth=GroundTruth(
                    target_abuse_class=AbuseClass.BRACKETING_ABUSE,
                    expected_decision=dec,
                    failure_case=False,
                    rationale=rationale
                )
            )

        elif abuse_kind == "serial":
            t = random.choice(self.serial_templates)
            title, cat, price, ord_cnt, ret_cnt, ret_rate, cb_cnt, rationale, dec = t
            cust_id = f"cust_live_ser_{uuid.uuid4().hex[:6]}"
            item = OrderItem(sku=f"SKU_LIVE_S_{uuid.uuid4().hex[:6]}", title=title, category=cat, unit_price=price, is_high_resale=True)
            return ReturnEvent(
                event_id=event_id,
                is_synthetic=True,
                split="live",
                timestamp=now_ts,
                customer_profile=CustomerProfile(
                    customer_id=cust_id,
                    account_age_days=random.randint(45, 250),
                    total_orders_count=ord_cnt,
                    total_returns_count=ret_cnt,
                    historical_return_rate=ret_rate,
                    past_return_reasons=["DID_NOT_LIKE"],
                    dispute_chargeback_count=cb_cnt
                ),
                order_details=OrderDetails(
                    order_id=f"ord_live_s_{uuid.uuid4().hex[:6]}",
                    order_date=now_ts,
                    days_since_purchase=2,
                    total_order_amount=price,
                    currency="INR",
                    payment_method="CREDIT_CARD",
                    items=[item]
                ),
                return_request=ReturnRequest(
                    return_id=f"req_live_s_{uuid.uuid4().hex[:6]}",
                    return_reason_code="DID_NOT_LIKE",
                    return_reason_notes="Dislike product performance.",
                    returned_items=[item],
                    requested_refund_amount=price,
                    refund_destination="ORIGINAL_PAYMENT_METHOD",
                    item_condition_tag="TAGS_ATTACHED"
                ),
                ground_truth=GroundTruth(
                    target_abuse_class=AbuseClass.SERIAL_RETURNER_FRAUD,
                    expected_decision=dec,
                    failure_case=False,
                    rationale=rationale
                )
            )

        else:
            t = random.choice(self.damage_templates)
            title, cat, price, age, pay_meth, ref_dest, cond, rationale, dec = t
            cust_id = f"cust_live_dmg_{uuid.uuid4().hex[:6]}"
            item = OrderItem(sku=f"SKU_LIVE_D_{uuid.uuid4().hex[:6]}", title=title, category=cat, unit_price=price, is_high_resale=True)
            return ReturnEvent(
                event_id=event_id,
                is_synthetic=True,
                split="live",
                timestamp=now_ts,
                customer_profile=CustomerProfile(
                    customer_id=cust_id,
                    account_age_days=age,
                    total_orders_count=1,
                    total_returns_count=0,
                    historical_return_rate=0.0,
                    past_return_reasons=["DEFECTIVE_DAMAGED"],
                    dispute_chargeback_count=0
                ),
                order_details=OrderDetails(
                    order_id=f"ord_live_d_{uuid.uuid4().hex[:6]}",
                    order_date=now_ts,
                    days_since_purchase=1,
                    total_order_amount=price,
                    currency="INR",
                    payment_method=pay_meth,
                    items=[item]
                ),
                return_request=ReturnRequest(
                    return_id=f"req_live_d_{uuid.uuid4().hex[:6]}",
                    return_reason_code="DEFECTIVE_DAMAGED",
                    return_reason_notes="Item arrived broken out of box, instant refund needed.",
                    returned_items=[item],
                    requested_refund_amount=price,
                    refund_destination=ref_dest,
                    item_condition_tag=cond
                ),
                ground_truth=GroundTruth(
                    target_abuse_class=AbuseClass.FALSE_DAMAGE_CLAIM,
                    expected_decision=dec,
                    failure_case=False,
                    rationale=rationale
                )
            )
