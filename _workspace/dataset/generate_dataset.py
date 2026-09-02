"""
Synthetic Dataset Generator for Return-Risk Shield (AI Risk Manager - Track 02).
Generates synthetic order/return event records (dev & held-out evaluation partitions).
Strictly compliant with _workspace/requirements/contracts.py.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

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


def create_base_time(offset_minutes: float = 0, offset_seconds: float = 0) -> str:
    base = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc) + timedelta(minutes=offset_minutes, seconds=offset_seconds)
    return base.isoformat().replace("+00:00", "Z")


def build_dev_dataset():
    cases = []
    
    # -------------------------------------------------------------
    # 1. DEV: Legitimate Returns (18 cases)
    # -------------------------------------------------------------
    legit_scenarios = [
        # (event_id, cust_id, age, orders, returns, rate, title, cat, price, days, reason_code, reason_notes, cond, rationale)
        ("ret_dev_001", "cust_dev_01", 360, 15, 2, 0.133, "Ergonomic Office Chair", "HOME_APPLIANCES", 8500, 3, "SIZE_FIT_ISSUE", "Seat depth slightly too large for my desk height", "UNOPENED", "Legitimate return by loyal customer within 3 days."),
        ("ret_dev_002", "cust_dev_02", 180, 8, 1, 0.125, "Running Shoes Size UK 9", "FOOTWEAR", 4200, 4, "SIZE_FIT_ISSUE", "Runs half a size small, exchanging for UK 9.5", "TAGS_ATTACHED", "Standard legitimate footwear size exchange."),
        ("ret_dev_003", "cust_dev_03", 420, 22, 3, 0.136, "Cotton Casual Shirt (Blue)", "FAST_FASHION", 1499, 2, "SIZE_FIT_ISSUE", "Chest fit is tight", "TAGS_ATTACHED", "Standard low-value apparel size issue."),
        ("ret_dev_004", "cust_dev_04", 90, 4, 0, 0.0, "Stainless Steel Water Flask 1L", "HOME_APPLIANCES", 899, 5, "DEFECTIVE_DAMAGED", "Vacuum seal cap leaking on first fill", "TAGS_ATTACHED", "Genuine defective accessory claim on clean account."),
        ("ret_dev_005", "cust_dev_05", 540, 30, 4, 0.133, "Wireless Mechanical Keyboard", "ELECTRONICS", 4500, 6, "DEFECTIVE_DAMAGED", "Spacebar key switch double-registering", "TAGS_ATTACHED", "Verified hardware defect return by established buyer."),
        ("ret_dev_006", "cust_dev_06", 210, 10, 1, 0.10, "A5 Hardcover Dotted Journal", "ACCESSORIES", 650, 1, "WRONG_ITEM_SENT", "Ordered dotted grid, received blank pages", "UNOPENED", "Merchant fulfillment error return."),
        ("ret_dev_007", "cust_dev_07", 300, 12, 2, 0.167, "Yoga Mat 6mm Non-Slip", "ACCESSORIES", 1299, 5, "DID_NOT_LIKE", "Color is lighter than catalog photo", "TAGS_ATTACHED", "Standard aesthetic preference return."),
        ("ret_dev_008", "cust_dev_08", 150, 6, 1, 0.167, "Ceramic Coffee Mug Set", "HOME_APPLIANCES", 799, 2, "DEFECTIVE_DAMAGED", "One handle cracked in transit", "TAGS_ATTACHED", "Transit damage on fragile tableware."),
        ("ret_dev_009", "cust_dev_09", 600, 25, 3, 0.12, "Aluminium Laptop Riser", "ACCESSORIES", 2450, 4, "SIZE_FIT_ISSUE", "Too wide for 13-inch MacBook", "TAGS_ATTACHED", "Legitimate workspace accessory return."),
        ("ret_dev_010", "cust_dev_10", 120, 5, 0, 0.0, "LED Desk Lamp with Qi Charger", "HOME_APPLIANCES", 2300, 3, "DEFECTIVE_DAMAGED", "Wireless charging pad intermittently disconnects", "TAGS_ATTACHED", "Legitimate electrical defect claim."),
        ("ret_dev_011", "cust_dev_11", 450, 18, 2, 0.111, "Men Formal Trousers 32W", "FAST_FASHION", 2199, 4, "SIZE_FIT_ISSUE", "Waist needs 34W", "TAGS_ATTACHED", "Normal formalwear size exchange."),
        ("ret_dev_012", "cust_dev_12", 270, 11, 1, 0.091, "Kids Denim Jacket", "FAST_FASHION", 1850, 5, "SIZE_FIT_ISSUE", "Sleeve length is short", "TAGS_ATTACHED", "Standard children's clothing return."),
        ("ret_dev_013", "cust_dev_13", 380, 16, 2, 0.125, "Blackout Curtains 7ft Pair", "HOME_APPLIANCES", 1999, 6, "SIZE_FIT_ISSUE", "Window requires 9ft length", "TAGS_ATTACHED", "Home decor measurement return."),
        ("ret_dev_014", "cust_dev_14", 720, 40, 5, 0.125, "Bluetooth Over-Ear Headphones", "ELECTRONICS", 6999, 4, "DID_NOT_LIKE", "Clamping force too tight for my head shape", "TAGS_ATTACHED", "Comfort return by high-LTV loyal customer."),
        ("ret_dev_015", "cust_dev_15", 160, 7, 1, 0.143, "Leather Laptop Backpack", "ACCESSORIES", 3499, 3, "SIZE_FIT_ISSUE", "Does not fit 16-inch gaming laptop", "TAGS_ATTACHED", "Sizing mismatch on accessory."),
        ("ret_dev_016", "cust_dev_16", 500, 20, 3, 0.15, "Non-Stick Cookware Pan 28cm", "HOME_APPLIANCES", 2200, 2, "WRONG_ITEM_SENT", "Received 24cm instead of 28cm", "UNOPENED", "Fulfillment mismatch on cookware."),
        ("ret_dev_017", "cust_dev_17", 95, 3, 0, 0.0, "Ankle Boots Size 38", "FOOTWEAR", 3800, 5, "SIZE_FIT_ISSUE", "Too narrow in toe box", "TAGS_ATTACHED", "Footwear fit return."),
        ("ret_dev_018", "cust_dev_18", 340, 14, 2, 0.143, "Smart Fitness Band 7", "ELECTRONICS", 3999, 3, "DEFECTIVE_DAMAGED", "Touchscreen unresponsive in top corner", "TAGS_ATTACHED", "Clean hardware defect return.")
    ]

    for idx, (ev_id, c_id, age, ord_cnt, ret_cnt, ret_rate, title, cat, price, days, code, notes, cond, rationale) in enumerate(legit_scenarios):
        item = OrderItem(sku=f"SKU_{idx+100:03d}", title=title, category=cat, unit_price=price, discount_pct=0.0)
        cases.append(ReturnEvent(
            event_id=ev_id,
            is_synthetic=True,
            split="dev",
            timestamp=create_base_time(idx * 3),
            customer_profile=CustomerProfile(
                customer_id=c_id,
                account_age_days=age,
                total_orders_count=ord_cnt,
                total_returns_count=ret_cnt,
                historical_return_rate=ret_rate,
                past_return_reasons=["SIZE_FIT_ISSUE"],
                dispute_chargeback_count=0
            ),
            order_details=OrderDetails(
                order_id=f"ord_dev_{idx+100:03d}",
                order_date=create_base_time(idx * 3 - days * 1440),
                days_since_purchase=days,
                total_order_amount=price,
                currency="INR",
                payment_method="UPI",
                items=[item]
            ),
            return_request=ReturnRequest(
                return_id=f"ret_req_{idx+100:03d}",
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
        ))

    # -------------------------------------------------------------
    # 2. DEV: Wardrobing Attacks (8 cases)
    # -------------------------------------------------------------
    wardrobe_scenarios = [
        ("ret_dev_019", "cust_ward_01", 120, 3, 2, 0.667, "Embroidered Silk Bridal Lehenga", "APPAREL_LUXURY", 28500, 27, "DID_NOT_LIKE", "Function is over, no longer needed", "TAGS_REMOVED", "Classic wardrobing: luxury wedding wear used for reception and returned on day 27 with tags removed.", DecisionAction.BLOCK),
        ("ret_dev_020", "cust_ward_02", 90, 2, 1, 0.50, "Italian Tuxedo Suit with Bow Tie", "APPAREL_LUXURY", 18900, 25, "DID_NOT_LIKE", "Attended annual gala, fit was slightly loose", "USED_ONCE", "Wardrobing: high-ticket tuxedo returned after single-use event on day 25.", DecisionAction.BLOCK),
        ("ret_dev_021", "cust_ward_03", 200, 5, 2, 0.40, "Designer Velvet Sherwani", "APPAREL_LUXURY", 22000, 24, "DID_NOT_LIKE", "Wedding ceremony completed", "TAGS_REMOVED", "Wardrobing: ceremony keyword and tags removed on luxury sherwani.", DecisionAction.BLOCK),
        ("ret_dev_022", "cust_ward_04", 150, 4, 2, 0.50, "High-End Cocktail Evening Gown", "APPAREL_LUXURY", 14500, 28, "DID_NOT_LIKE", "Photoshoot finished, color looked different on camera", "USED_ONCE", "Wardrobing: photoshoot single use on designer gown.", DecisionAction.BLOCK),
        ("ret_dev_023", "cust_ward_05", 80, 2, 1, 0.50, "Pure Pashmina Kashmiri Shawl", "APPAREL_LUXURY", 12500, 26, "DID_NOT_LIKE", "Winter holiday over", "HEAVILY_WORN", "Wardrobing: luxury winter shawl returned heavily worn on day 26.", DecisionAction.BLOCK),
        ("ret_dev_024", "cust_ward_06", 110, 4, 1, 0.25, "Gold Zari Banarasi Saree", "APPAREL_LUXURY", 16000, 22, "DID_NOT_LIKE", "Color looked different in indoor stage lights", "USED_ONCE", "Wardrobing flag: luxury saree used at event and returned on day 22.", DecisionAction.FLAG),
        ("ret_dev_025", "cust_ward_07", 140, 5, 2, 0.40, "Custom Tailored Bandhgala Blazer", "APPAREL_LUXURY", 11999, 21, "DID_NOT_LIKE", "Used for family party", "USED_ONCE", "Wardrobing flag: luxury blazer returned after event.", DecisionAction.FLAG),
        ("ret_dev_026", "cust_ward_08", 95, 3, 1, 0.333, "Sequin Party Wear Jumpsuit", "FAST_FASHION", 7500, 20, "DID_NOT_LIKE", "New Year party outfit no longer needed", "USED_ONCE", "Wardrobing flag: festive occasionwear returned after event.", DecisionAction.FLAG),
    ]

    for idx, (ev_id, c_id, age, ord_cnt, ret_cnt, ret_rate, title, cat, price, days, code, notes, cond, rationale, dec) in enumerate(wardrobe_scenarios):
        item = OrderItem(sku=f"SKU_WARD_{idx+1:02d}", title=title, category=cat, unit_price=price, discount_pct=0.0)
        cases.append(ReturnEvent(
            event_id=ev_id,
            is_synthetic=True,
            split="dev",
            timestamp=create_base_time(60 + idx * 3),
            customer_profile=CustomerProfile(
                customer_id=c_id,
                account_age_days=age,
                total_orders_count=ord_cnt,
                total_returns_count=ret_cnt,
                historical_return_rate=ret_rate,
                past_return_reasons=["DID_NOT_LIKE"],
                dispute_chargeback_count=0
            ),
            order_details=OrderDetails(
                order_id=f"ord_ward_{idx+1:02d}",
                order_date=create_base_time(60 + idx * 3 - days * 1440),
                days_since_purchase=days,
                total_order_amount=price,
                currency="INR",
                payment_method="CREDIT_CARD",
                items=[item]
            ),
            return_request=ReturnRequest(
                return_id=f"ret_ward_{idx+1:02d}",
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
        ))

    # -------------------------------------------------------------
    # 3. DEV: Bracketing Abuse (8 cases)
    # -------------------------------------------------------------
    bracket_scenarios = [
        # Multi-size or multi-color ordering with bulk return
        ("ret_dev_027", "cust_brk_01", 150, 4, 2, 0.50, "Italian Leather Boots", "FOOTWEAR", 8500, [("SKU_BT_41", "Italian Leather Boots - Size 41", "41", "Brown"), ("SKU_BT_42", "Italian Leather Boots - Size 42", "42", "Brown"), ("SKU_BT_43", "Italian Leather Boots - Size 43", "43", "Brown")], 2, "Bracketing: ordered 3 shoe sizes simultaneously, returning 2.", DecisionAction.FLAG),
        ("ret_dev_028", "cust_brk_02", 180, 6, 3, 0.50, "Premium Merino Wool Blazer", "APPAREL_LUXURY", 12000, [("SKU_BLZ_38", "Premium Merino Wool Blazer - Size 38", "38", "Navy"), ("SKU_BLZ_40", "Premium Merino Wool Blazer - Size 40", "40", "Navy"), ("SKU_BLZ_42", "Premium Merino Wool Blazer - Size 42", "42", "Navy")], 2, "Bracketing: ordered 3 sizes of luxury blazer, returning 2.", DecisionAction.FLAG),
        ("ret_dev_029", "cust_brk_03", 210, 5, 3, 0.60, "Silk Evening Maxi Dress", "FAST_FASHION", 4500, [("SKU_DRS_S", "Silk Evening Maxi Dress - Size S", "S", "Emerald"), ("SKU_DRS_M", "Silk Evening Maxi Dress - Size M", "M", "Emerald"), ("SKU_DRS_L", "Silk Evening Maxi Dress - Size L", "L", "Emerald")], 2, "Bracketing abuse: ordering S, M, L to try at home and returning 2.", DecisionAction.FLAG),
        ("ret_dev_030", "cust_brk_04", 90, 3, 2, 0.667, "Suede Chelsea Boots", "FOOTWEAR", 6500, [("SKU_CHL_BLK", "Suede Chelsea Boots - Black", "42", "Black"), ("SKU_CHL_TAN", "Suede Chelsea Boots - Tan", "42", "Tan")], 1, "Color bracketing: ordered Black & Tan to choose one in person.", DecisionAction.FLAG),
        ("ret_dev_031", "cust_brk_05", 300, 8, 5, 0.625, "Linen Casual Shirt", "FAST_FASHION", 2200, [("SKU_SH_M", "Linen Casual Shirt - Size M", "M", "White"), ("SKU_SH_L", "Linen Casual Shirt - Size L", "L", "White"), ("SKU_SH_XL", "Linen Casual Shirt - Size XL", "XL", "White")], 2, "Chronic bracketing on fast fashion shirts.", DecisionAction.FLAG),
        ("ret_dev_032", "cust_brk_06", 140, 4, 3, 0.75, "High-Waisted Denim Jeans", "FAST_FASHION", 3200, [("SKU_JN_28", "High-Waisted Denim Jeans - Size 28", "28", "Blue"), ("SKU_JN_30", "High-Waisted Denim Jeans - Size 30", "30", "Blue"), ("SKU_JN_32", "High-Waisted Denim Jeans - Size 32", "32", "Blue")], 3, "Extreme bracketing: ordered 3 sizes and returning all 3 (+ 75% historical return rate).", DecisionAction.BLOCK),
        ("ret_dev_033", "cust_brk_07", 70, 2, 2, 1.0, "Designer Bomber Jacket", "APPAREL_LUXURY", 9500, [("SKU_BMB_S", "Designer Bomber Jacket - Size S", "S", "Olive"), ("SKU_BMB_M", "Designer Bomber Jacket - Size M", "M", "Olive")], 2, "Bracketing with 100% historical return rate.", DecisionAction.BLOCK),
        ("ret_dev_034", "cust_brk_08", 120, 3, 2, 0.667, "Waterproof Trekking Shoes", "FOOTWEAR", 5500, [("SKU_TRK_8", "Waterproof Trekking Shoes - Size 8", "8", "Grey"), ("SKU_TRK_9", "Waterproof Trekking Shoes - Size 9", "9", "Grey"), ("SKU_TRK_10", "Waterproof Trekking Shoes - Size 10", "10", "Grey")], 2, "Size bracketing on heavy footwear.", DecisionAction.FLAG),
    ]

    for idx, (ev_id, c_id, age, ord_cnt, ret_cnt, ret_rate, base_title, cat, price, variants, ret_count, rationale, dec) in enumerate(bracket_scenarios):
        order_items = [OrderItem(sku=v[0], title=v[1], category=cat, unit_price=price, size_variant=v[2], color_variant=v[3]) for v in variants]
        returned_items = order_items[:ret_count]
        total_order_amt = price * len(order_items)
        refund_amt = price * ret_count
        cases.append(ReturnEvent(
            event_id=ev_id,
            is_synthetic=True,
            split="dev",
            timestamp=create_base_time(90 + idx * 3),
            customer_profile=CustomerProfile(
                customer_id=c_id,
                account_age_days=age,
                total_orders_count=ord_cnt,
                total_returns_count=ret_cnt,
                historical_return_rate=ret_rate,
                past_return_reasons=["SIZE_FIT_ISSUE"],
                dispute_chargeback_count=0
            ),
            order_details=OrderDetails(
                order_id=f"ord_brk_{idx+1:02d}",
                order_date=create_base_time(90 + idx * 3 - 4 * 1440),
                days_since_purchase=4,
                total_order_amount=total_order_amt,
                currency="INR",
                payment_method="UPI",
                items=order_items
            ),
            return_request=ReturnRequest(
                return_id=f"ret_brk_{idx+1:02d}",
                return_reason_code="SIZE_FIT_ISSUE",
                return_reason_notes=f"Bracketed sizing trial: keeping best fit and returning {ret_count} other variant(s).",
                returned_items=returned_items,
                requested_refund_amount=refund_amt,
                refund_destination="ORIGINAL_PAYMENT_METHOD",
                item_condition_tag="TAGS_ATTACHED"
            ),
            ground_truth=GroundTruth(
                target_abuse_class=AbuseClass.BRACKETING_ABUSE,
                expected_decision=dec,
                failure_case=False,
                rationale=rationale
            )
        ))

    # -------------------------------------------------------------
    # 4. DEV: Serial Returner Fraud & Chronic Abuse (6 cases)
    # -------------------------------------------------------------
    serial_scenarios = [
        ("ret_dev_035", "cust_ser_01", 180, 10, 8, 0.80, 2, "Pro Gaming Mouse", "ELECTRONICS", 4999, "Serial returner: 80% return rate + 2 prior chargebacks.", DecisionAction.BLOCK),
        ("ret_dev_036", "cust_ser_02", 90, 6, 5, 0.833, 1, "4K Action Camera Kit", "ELECTRONICS", 14500, "Serial returner: 83.3% return rate + prior payment dispute.", DecisionAction.BLOCK),
        ("ret_dev_037", "cust_ser_03", 240, 12, 10, 0.833, 0, "Noise Canceling Earbuds", "ELECTRONICS", 8999, "Chronic returner: 10 returns across 12 orders (83.3%).", DecisionAction.BLOCK),
        ("ret_dev_038", "cust_ser_04", 45, 4, 3, 0.75, 0, "Ultra Wide Gaming Monitor", "ELECTRONICS", 24000, "High velocity serial returner on high-ticket monitors.", DecisionAction.BLOCK),
        ("ret_dev_039", "cust_ser_05", 300, 15, 7, 0.467, 1, "Smart Home Security Camera", "ELECTRONICS", 5500, "Elevated return rate (46.7%) + 1 chargeback.", DecisionAction.FLAG),
        ("ret_dev_040", "cust_ser_06", 160, 8, 4, 0.50, 0, "Electric Rotary Shaver", "HOME_APPLIANCES", 3200, "Elevated return velocity (50%) on personal grooming items.", DecisionAction.FLAG),
    ]

    for idx, (ev_id, c_id, age, ord_cnt, ret_cnt, ret_rate, cb_cnt, title, cat, price, rationale, dec) in enumerate(serial_scenarios):
        item = OrderItem(sku=f"SKU_SER_{idx+1:02d}", title=title, category=cat, unit_price=price, is_high_resale=True)
        cases.append(ReturnEvent(
            event_id=ev_id,
            is_synthetic=True,
            split="dev",
            timestamp=create_base_time(120 + idx * 3),
            customer_profile=CustomerProfile(
                customer_id=c_id,
                account_age_days=age,
                total_orders_count=ord_cnt,
                total_returns_count=ret_cnt,
                historical_return_rate=ret_rate,
                past_return_reasons=["DID_NOT_LIKE", "DEFECTIVE_DAMAGED"],
                dispute_chargeback_count=cb_cnt
            ),
            order_details=OrderDetails(
                order_id=f"ord_ser_{idx+1:02d}",
                order_date=create_base_time(120 + idx * 3 - 3 * 1440),
                days_since_purchase=3,
                total_order_amount=price,
                currency="INR",
                payment_method="CREDIT_CARD",
                items=[item]
            ),
            return_request=ReturnRequest(
                return_id=f"ret_ser_{idx+1:02d}",
                return_reason_code="DID_NOT_LIKE",
                return_reason_notes="Not satisfied with performance, requesting full refund.",
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
        ))

    # -------------------------------------------------------------
    # 5. DEV: False Damage Claims & Arbitrage (6 cases)
    # -------------------------------------------------------------
    damage_scenarios = [
        ("ret_dev_041", "cust_dmg_01", 12, 1, 0, 0.0, "Flagship Smartphone 256GB", "ELECTRONICS", 65000, "COD", "INSTANT_CASH", "MISSING_PARTS", "False damage/swap claim: Day 12 account, ₹65,000 phone on COD requesting instant cash refund with missing parts tag.", DecisionAction.BLOCK),
        ("ret_dev_042", "cust_dmg_02", 20, 2, 1, 0.50, "Wireless Noise Canceling ANC Headphones", "ELECTRONICS", 18990, "COD", "INSTANT_BANK_TRANSFER", "TAGS_ATTACHED", "High-resale electronics false damage claim by 20-day account demanding instant cash transfer.", DecisionAction.BLOCK),
        ("ret_dev_043", "cust_dmg_03", 15, 1, 0, 0.0, "Portable SSD 2TB Extreme", "ELECTRONICS", 14500, "COD", "INSTANT_CASH", "MISSING_PARTS", "Empty box / component swap risk on high-value portable SSD.", DecisionAction.BLOCK),
        ("ret_dev_044", "cust_dmg_04", 180, 8, 3, 0.375, "4K Drone with Gimbal Camera", "ELECTRONICS", 28000, "CREDIT_CARD", "ORIGINAL_PAYMENT_METHOD", "TAGS_ATTACHED", "High-value drone damage claim by elevated-return customer. Requires hardware inspection.", DecisionAction.FLAG),
        ("ret_dev_045", "cust_dmg_05", 90, 4, 1, 0.25, "Smart Watch Ultra Titanium", "ELECTRONICS", 32000, "UPI", "ORIGINAL_PAYMENT_METHOD", "TAGS_ATTACHED", "High-ticket smartwatch damage claim. Routed for serial verification.", DecisionAction.FLAG),
        ("ret_dev_046", "cust_dmg_06", 140, 6, 2, 0.333, "Mirrorless Digital Camera Body", "ELECTRONICS", 54000, "CREDIT_CARD", "ORIGINAL_PAYMENT_METHOD", "TAGS_ATTACHED", "High-resale camera damage claim. Requires authorized service center check.", DecisionAction.FLAG),
    ]

    for idx, (ev_id, c_id, age, ord_cnt, ret_cnt, ret_rate, title, cat, price, pay_meth, ref_dest, cond, rationale, dec) in enumerate(damage_scenarios):
        item = OrderItem(sku=f"SKU_DMG_{idx+1:02d}", title=title, category=cat, unit_price=price, is_high_resale=True)
        cases.append(ReturnEvent(
            event_id=ev_id,
            is_synthetic=True,
            split="dev",
            timestamp=create_base_time(150 + idx * 3),
            customer_profile=CustomerProfile(
                customer_id=c_id,
                account_age_days=age,
                total_orders_count=ord_cnt,
                total_returns_count=ret_cnt,
                historical_return_rate=ret_rate,
                past_return_reasons=["DEFECTIVE_DAMAGED"],
                dispute_chargeback_count=0
            ),
            order_details=OrderDetails(
                order_id=f"ord_dmg_{idx+1:02d}",
                order_date=create_base_time(150 + idx * 3 - 2 * 1440),
                days_since_purchase=2,
                total_order_amount=price,
                currency="INR",
                payment_method=pay_meth,
                items=[item]
            ),
            return_request=ReturnRequest(
                return_id=f"ret_dmg_{idx+1:02d}",
                return_reason_code="DEFECTIVE_DAMAGED",
                return_reason_notes="Arrived non-functional out of the box, requesting immediate refund clearance.",
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
        ))

    return cases


def build_heldout_dataset():
    cases = []
    
    # -------------------------------------------------------------
    # 1. HELDOUT: Legitimate Returns (12 cases)
    # -------------------------------------------------------------
    heldout_legit = [
        ("ret_eval_001", "cust_eval_01", 400, 18, 2, 0.111, "Ergonomic Vertical Mouse", "ACCESSORIES", 2750, 4, "SIZE_FIT_ISSUE", "Grip is too small for my hand size", "TAGS_ATTACHED", "Legitimate ergonomic accessory return."),
        ("ret_eval_002", "cust_eval_02", 280, 12, 1, 0.083, "Podcast Condenser Microphone", "ELECTRONICS", 6499, 5, "DID_NOT_LIKE", "Picks up too much room echo in unpadded room", "TAGS_ATTACHED", "Legitimate acoustic compatibility return."),
        ("ret_eval_003", "cust_eval_03", 520, 24, 3, 0.125, "Dual Monitor Desk Mount", "HOME_APPLIANCES", 4499, 3, "SIZE_FIT_ISSUE", "Clamp does not fit beveled desk edge", "TAGS_ATTACHED", "Standard hardware fit issue."),
        ("ret_eval_004", "cust_eval_04", 190, 8, 1, 0.125, "Pastel Sticky Note Cubes (12-Pack)", "ACCESSORIES", 1050, 2, "WRONG_ITEM_SENT", "Received neon colors instead of pastel", "UNOPENED", "Legitimate merchant fulfillment error."),
        ("ret_eval_005", "cust_eval_05", 310, 14, 2, 0.143, "Smart Dimmable LED Desk Lamp", "HOME_APPLIANCES", 2999, 4, "DID_NOT_LIKE", "Color temperature does not go as warm as desired", "TAGS_ATTACHED", "Standard aesthetic preference return on clean profile."),
        ("ret_eval_006", "cust_eval_06", 160, 6, 0, 0.0, "Dual Dynamic In-Ear Earphones", "ELECTRONICS", 1850, 3, "DEFECTIVE_DAMAGED", "Left earbud has static hum", "TAGS_ATTACHED", "Legitimate low-cost earphone defect on new clean profile."),
        ("ret_eval_007", "cust_eval_07", 450, 20, 2, 0.10, "Under Desk Cable Management Tray", "HOME_APPLIANCES", 1499, 2, "SIZE_FIT_ISSUE", "Desk frame has crossbar blocking installation", "TAGS_ATTACHED", "Legitimate workspace accessory return."),
        ("ret_eval_008", "cust_eval_08", 230, 9, 1, 0.111, "Wireless Presentation Remote", "ACCESSORIES", 1299, 3, "DID_NOT_LIKE", "Laser pointer button placement awkward", "TAGS_ATTACHED", "Legitimate business tool return."),
        ("ret_eval_009", "cust_eval_09", 600, 28, 4, 0.143, "24-Inch Privacy Screen Filter", "ACCESSORIES", 2399, 4, "SIZE_FIT_ISSUE", "Does not adhere properly to curved screen bezel", "TAGS_ATTACHED", "Legitimate display accessory return."),
        ("ret_eval_010", "cust_eval_10", 350, 15, 1, 0.067, "65W GaN Dual Port Wall Charger", "ELECTRONICS", 3199, 5, "DEFECTIVE_DAMAGED", "Secondary USB-C port does not fast charge", "TAGS_ATTACHED", "Legitimate charger defect on established account."),
        ("ret_eval_011", "cust_eval_11", 180, 7, 1, 0.143, "Magnetic Whiteboard 60x45cm", "HOME_APPLIANCES", 1390, 2, "DEFECTIVE_DAMAGED", "Corner bent during courier transit", "TAGS_ATTACHED", "Transit damage on office furniture."),
        ("ret_eval_012", "cust_eval_12", 480, 22, 3, 0.136, "Ergonomic Gel Mousepad", "ACCESSORIES", 850, 3, "DID_NOT_LIKE", "Gel rest is too firm for my preference", "TAGS_ATTACHED", "Standard accessory return.")
    ]

    for idx, (ev_id, c_id, age, ord_cnt, ret_cnt, ret_rate, title, cat, price, days, code, notes, cond, rationale) in enumerate(heldout_legit):
        item = OrderItem(sku=f"SKU_EVAL_L_{idx+1:02d}", title=title, category=cat, unit_price=price, discount_pct=0.0)
        cases.append(ReturnEvent(
            event_id=ev_id,
            is_synthetic=True,
            split="heldout_eval",
            timestamp=create_base_time(200 + idx * 4),
            customer_profile=CustomerProfile(
                customer_id=c_id,
                account_age_days=age,
                total_orders_count=ord_cnt,
                total_returns_count=ret_cnt,
                historical_return_rate=ret_rate,
                past_return_reasons=["SIZE_FIT_ISSUE"],
                dispute_chargeback_count=0
            ),
            order_details=OrderDetails(
                order_id=f"ord_eval_{idx+1:02d}",
                order_date=create_base_time(200 + idx * 4 - days * 1440),
                days_since_purchase=days,
                total_order_amount=price,
                currency="INR",
                payment_method="UPI",
                items=[item]
            ),
            return_request=ReturnRequest(
                return_id=f"ret_eval_{idx+1:02d}",
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
        ))

    # -------------------------------------------------------------
    # 2. HELDOUT: Wardrobing Attacks (4 cases)
    # -------------------------------------------------------------
    heldout_wardrobe = [
        ("ret_eval_013", "cust_eval_w1", 110, 3, 2, 0.667, "Pure Raw Silk Festive Lehenga", "APPAREL_LUXURY", 32000, 28, "DID_NOT_LIKE", "Sister wedding reception over, color slightly bright", "TAGS_REMOVED", "High-confidence Wardrobing: ₹32k luxury lehenga returned on day 28 with tags removed after wedding.", DecisionAction.BLOCK),
        ("ret_eval_014", "cust_eval_w2", 85, 2, 1, 0.50, "Bespoke Italian Double Breasted Tuxedo", "APPAREL_LUXURY", 24000, 26, "DID_NOT_LIKE", "Attended corporate awards ceremony, fit felt tight", "USED_ONCE", "Wardrobing: luxury tuxedo used for awards function and returned on day 26.", DecisionAction.BLOCK),
        ("ret_eval_015", "cust_eval_w3", 150, 4, 1, 0.25, "Handwoven Kanjeevaram Saree", "APPAREL_LUXURY", 19500, 24, "DID_NOT_LIKE", "Worn to family function", "USED_ONCE", "Wardrobing flag: luxury saree worn to family event and returned on day 24.", DecisionAction.FLAG),
        ("ret_eval_016", "cust_eval_w4", 95, 3, 1, 0.333, "Velvet Designer Anarkali Suit", "APPAREL_LUXURY", 13500, 22, "DID_NOT_LIKE", "Sangeet ceremony finished", "USED_ONCE", "Wardrobing flag: occasionwear returned after event.", DecisionAction.FLAG),
    ]

    for idx, (ev_id, c_id, age, ord_cnt, ret_cnt, ret_rate, title, cat, price, days, code, notes, cond, rationale, dec) in enumerate(heldout_wardrobe):
        item = OrderItem(sku=f"SKU_EVAL_W_{idx+1:02d}", title=title, category=cat, unit_price=price)
        cases.append(ReturnEvent(
            event_id=ev_id,
            is_synthetic=True,
            split="heldout_eval",
            timestamp=create_base_time(250 + idx * 4),
            customer_profile=CustomerProfile(
                customer_id=c_id,
                account_age_days=age,
                total_orders_count=ord_cnt,
                total_returns_count=ret_cnt,
                historical_return_rate=ret_rate,
                past_return_reasons=["DID_NOT_LIKE"],
                dispute_chargeback_count=0
            ),
            order_details=OrderDetails(
                order_id=f"ord_eval_w_{idx+1:02d}",
                order_date=create_base_time(250 + idx * 4 - days * 1440),
                days_since_purchase=days,
                total_order_amount=price,
                currency="INR",
                payment_method="CREDIT_CARD",
                items=[item]
            ),
            return_request=ReturnRequest(
                return_id=f"ret_eval_w_{idx+1:02d}",
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
        ))

    # -------------------------------------------------------------
    # 3. HELDOUT: Bracketing Abuse (4 cases)
    # -------------------------------------------------------------
    heldout_bracket = [
        ("ret_eval_017", "cust_eval_b1", 160, 5, 3, 0.60, "Italian Leather Derby Shoes", "FOOTWEAR", 7800, [("SKU_DRB_41", "Italian Leather Derby Shoes - Size 41", "41", "Black"), ("SKU_DRB_42", "Italian Leather Derby Shoes - Size 42", "42", "Black"), ("SKU_DRB_43", "Italian Leather Derby Shoes - Size 43", "43", "Black")], 2, "Bracketing abuse: ordered 3 sizes of luxury derby shoes and returning 2.", DecisionAction.FLAG),
        ("ret_eval_018", "cust_eval_b2", 130, 4, 3, 0.75, "Tailored Linen Summer Blazer", "APPAREL_LUXURY", 11500, [("SKU_BLZ_38", "Tailored Linen Summer Blazer - Size 38", "38", "Beige"), ("SKU_BLZ_40", "Tailored Linen Summer Blazer - Size 40", "40", "Beige"), ("SKU_BLZ_42", "Tailored Linen Summer Blazer - Size 42", "42", "Beige")], 3, "Severe bracketing: ordered 3 sizes of ₹11,500 blazer and returning all 3 (75% return rate).", DecisionAction.BLOCK),
        ("ret_eval_019", "cust_eval_b3", 95, 3, 2, 0.667, "Merino Wool Knit Sweater", "FAST_FASHION", 3800, [("SKU_SWT_M", "Merino Wool Knit Sweater - Size M", "M", "Navy"), ("SKU_SWT_L", "Merino Wool Knit Sweater - Size L", "L", "Navy")], 1, "Size bracketing on knit sweaters.", DecisionAction.FLAG),
        ("ret_eval_020", "cust_eval_b4", 210, 6, 4, 0.667, "Premium Ankle Chelsea Boots", "FOOTWEAR", 6200, [("SKU_CH_BLK", "Premium Ankle Chelsea Boots - Black", "42", "Black"), ("SKU_CH_BRN", "Premium Ankle Chelsea Boots - Brown", "42", "Brown")], 1, "Color bracketing: bought black and brown pair, returning one.", DecisionAction.FLAG),
    ]

    for idx, (ev_id, c_id, age, ord_cnt, ret_cnt, ret_rate, base_title, cat, price, variants, ret_count, rationale, dec) in enumerate(heldout_bracket):
        order_items = [OrderItem(sku=v[0], title=v[1], category=cat, unit_price=price, size_variant=v[2], color_variant=v[3]) for v in variants]
        returned_items = order_items[:ret_count]
        cases.append(ReturnEvent(
            event_id=ev_id,
            is_synthetic=True,
            split="heldout_eval",
            timestamp=create_base_time(280 + idx * 4),
            customer_profile=CustomerProfile(
                customer_id=c_id,
                account_age_days=age,
                total_orders_count=ord_cnt,
                total_returns_count=ret_cnt,
                historical_return_rate=ret_rate,
                past_return_reasons=["SIZE_FIT_ISSUE"],
                dispute_chargeback_count=0
            ),
            order_details=OrderDetails(
                order_id=f"ord_eval_b_{idx+1:02d}",
                order_date=create_base_time(280 + idx * 4 - 3 * 1440),
                days_since_purchase=3,
                total_order_amount=price * len(order_items),
                currency="INR",
                payment_method="UPI",
                items=order_items
            ),
            return_request=ReturnRequest(
                return_id=f"ret_eval_b_{idx+1:02d}",
                return_reason_code="SIZE_FIT_ISSUE",
                return_reason_notes=f"Bracket trial: returning {ret_count} unneeded variant(s).",
                returned_items=returned_items,
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
        ))

    # -------------------------------------------------------------
    # 4. HELDOUT: Serial Returner Fraud (4 cases)
    # -------------------------------------------------------------
    heldout_serial = [
        ("ret_eval_021", "cust_eval_s1", 190, 11, 9, 0.818, 2, "Pro Streaming USB Microphone", "ELECTRONICS", 7500, "Serial returner fraud: 81.8% return rate + 2 prior chargebacks.", DecisionAction.BLOCK),
        ("ret_eval_022", "cust_eval_s2", 140, 8, 7, 0.875, 1, "Active Studio Reference Monitors", "ELECTRONICS", 18500, "Chronic serial returner: 87.5% return rate + chargeback on audio gear.", DecisionAction.BLOCK),
        ("ret_eval_023", "cust_eval_s3", 260, 14, 11, 0.786, 0, "4K Ultra-Wide Monitor", "ELECTRONICS", 32000, "High velocity serial returner on high-ticket monitors (78.6% return rate).", DecisionAction.BLOCK),
        ("ret_eval_024", "cust_eval_s4", 175, 9, 5, 0.556, 0, "Mechanical Gaming Keyboard RGB", "ELECTRONICS", 5800, "Elevated return rate (55.6%) on gaming peripherals.", DecisionAction.FLAG),
    ]

    for idx, (ev_id, c_id, age, ord_cnt, ret_cnt, ret_rate, cb_cnt, title, cat, price, rationale, dec) in enumerate(heldout_serial):
        item = OrderItem(sku=f"SKU_EVAL_S_{idx+1:02d}", title=title, category=cat, unit_price=price, is_high_resale=True)
        cases.append(ReturnEvent(
            event_id=ev_id,
            is_synthetic=True,
            split="heldout_eval",
            timestamp=create_base_time(300 + idx * 4),
            customer_profile=CustomerProfile(
                customer_id=c_id,
                account_age_days=age,
                total_orders_count=ord_cnt,
                total_returns_count=ret_cnt,
                historical_return_rate=ret_rate,
                past_return_reasons=["DID_NOT_LIKE"],
                dispute_chargeback_count=cb_cnt
            ),
            order_details=OrderDetails(
                order_id=f"ord_eval_s_{idx+1:02d}",
                order_date=create_base_time(300 + idx * 4 - 3 * 1440),
                days_since_purchase=3,
                total_order_amount=price,
                currency="INR",
                payment_method="CREDIT_CARD",
                items=[item]
            ),
            return_request=ReturnRequest(
                return_id=f"ret_eval_s_{idx+1:02d}",
                return_reason_code="DID_NOT_LIKE",
                return_reason_notes="Not satisfied with device.",
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
        ))

    # -------------------------------------------------------------
    # 5. HELDOUT: False Damage Claims & Arbitrage (3 cases)
    # -------------------------------------------------------------
    heldout_damage = [
        ("ret_eval_025", "cust_eval_d1", 10, 1, 0, 0.0, "Flagship Smartwatch Cellular 49mm", "ELECTRONICS", 45000, "COD", "INSTANT_CASH", "MISSING_PARTS", "False damage/swap claim: 10-day old account ordering ₹45,000 smartwatch via COD demanding instant cash refund with missing parts tag.", DecisionAction.BLOCK),
        ("ret_eval_026", "cust_eval_d2", 15, 1, 0, 0.0, "Ultra Fast NVMe Portable SSD 2TB", "ELECTRONICS", 16900, "COD", "INSTANT_CASH", "MISSING_PARTS", "Empty box / component swap risk on high-value portable SSD on COD.", DecisionAction.BLOCK),
        ("ret_eval_027", "cust_eval_d3", 120, 5, 2, 0.40, "Compact Action Camera 4K60", "ELECTRONICS", 22500, "UPI", "ORIGINAL_PAYMENT_METHOD", "TAGS_ATTACHED", "High-ticket action camera damage claim by elevated-return customer. Requires inspection.", DecisionAction.FLAG),
    ]

    for idx, (ev_id, c_id, age, ord_cnt, ret_cnt, ret_rate, title, cat, price, pay_meth, ref_dest, cond, rationale, dec) in enumerate(heldout_damage):
        item = OrderItem(sku=f"SKU_EVAL_D_{idx+1:02d}", title=title, category=cat, unit_price=price, is_high_resale=True)
        cases.append(ReturnEvent(
            event_id=ev_id,
            is_synthetic=True,
            split="heldout_eval",
            timestamp=create_base_time(320 + idx * 4),
            customer_profile=CustomerProfile(
                customer_id=c_id,
                account_age_days=age,
                total_orders_count=ord_cnt,
                total_returns_count=ret_cnt,
                historical_return_rate=ret_rate,
                past_return_reasons=["DEFECTIVE_DAMAGED"],
                dispute_chargeback_count=0
            ),
            order_details=OrderDetails(
                order_id=f"ord_eval_d_{idx+1:02d}",
                order_date=create_base_time(320 + idx * 4 - 2 * 1440),
                days_since_purchase=2,
                total_order_amount=price,
                currency="INR",
                payment_method=pay_meth,
                items=[item]
            ),
            return_request=ReturnRequest(
                return_id=f"ret_eval_d_{idx+1:02d}",
                return_reason_code="DEFECTIVE_DAMAGED",
                return_reason_notes="Defective unit on arrival, requesting instant refund clearance.",
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
        ))

    # -------------------------------------------------------------
    # 6. HELDOUT: Documented Honest Failure Case (1 case)
    # -------------------------------------------------------------
    # Borderline Case: Long-time loyal customer returning luxury occasionwear at day 14
    # with tags re-attached after subtle wear.
    item_fail = OrderItem(sku="SKU_FAIL_SAR_01", title="Handcrafted Kanjeevaram Pure Silk Wedding Saree", category="APPAREL_LUXURY", unit_price=18500.0, is_high_resale=False)
    cases.append(ReturnEvent(
        event_id="ret_synth_fail_001",
        is_synthetic=True,
        split="heldout_eval",
        timestamp=create_base_time(340),
        customer_profile=CustomerProfile(
            customer_id="cust_loyal_edge_01",
            account_age_days=420,
            total_orders_count=14,
            total_returns_count=3,
            historical_return_rate=0.214,
            past_return_reasons=["SIZE_FIT_ISSUE"],
            dispute_chargeback_count=0
        ),
        order_details=OrderDetails(
            order_id="ord_fail_001",
            order_date=create_base_time(340 - 14 * 1440),
            days_since_purchase=14,
            total_order_amount=18500.0,
            currency="INR",
            payment_method="CREDIT_CARD",
            items=[item_fail]
        ),
        return_request=ReturnRequest(
            return_id="ret_req_fail_001",
            return_reason_code="DID_NOT_LIKE",
            return_reason_notes="Color tone under banquet hall lighting did not match bridesmaid theme.",
            returned_items=[item_fail],
            requested_refund_amount=18500.0,
            refund_destination="ORIGINAL_PAYMENT_METHOD",
            item_condition_tag="TAGS_ATTACHED"
        ),
        ground_truth=GroundTruth(
            target_abuse_class=AbuseClass.WARDROBING,
            expected_decision=DecisionAction.FLAG,
            failure_case=True,
            rationale="Honest Failure Case: Keyword evasion in wardrobing detection. The buyer wore a ₹18,500 bridal silk saree to an event, kept the swing tag attached ('TAGS_ATTACHED'), and returned it on Day 14 describing the reason as 'Color tone under banquet hall lighting did not match bridesmaid theme'. This phrasing omitted exact keyword triggers ('wedding', 'reception', 'party', 'gala', 'ceremony'). Combined with days_since_purchase = 14 (< 18 cutoff) and a clean account history (21.4% return rate), all deterministic checks passed, outputting ALLOW (False Negative) against the expected FLAG ground truth."
        )
    ))

    return cases


def main():
    dev_cases = build_dev_dataset()
    heldout_cases = build_heldout_dataset()
    
    os.makedirs("_workspace/dataset", exist_ok=True)
    
    dev_path = "_workspace/dataset/dev_transactions.json"
    heldout_path = "_workspace/dataset/heldout_eval_transactions.json"
    
    with open(dev_path, "w") as f:
        json.dump([c.model_dump() for c in dev_cases], f, indent=2)
        
    with open(heldout_path, "w") as f:
        json.dump([c.model_dump() for c in heldout_cases], f, indent=2)
        
    print(f"Successfully generated {len(dev_cases)} dev return cases -> {dev_path}")
    print(f"Successfully generated {len(heldout_cases)} held-out evaluation return cases -> {heldout_path}")
    print(f"Total synthetic dataset: {len(dev_cases) + len(heldout_cases)} cases (Strict Dev vs Held-Out split)")


if __name__ == "__main__":
    main()
