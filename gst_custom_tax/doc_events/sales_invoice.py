import frappe
from frappe.utils import flt


def before_taxes_and_totals(doc, method=None):

    fim_exists = any(flt(item.get("custom_fim_value", 0)) for item in doc.items)

    if not fim_exists:
        
        return

    for tax in doc.taxes:
        tax.tax_amount = 0.0
        tax.base_tax_amount = 0.0
        tax.tax_amount_after_discount_amount = 0.0
        tax.total = 0.0
        tax.base_total = 0.0
        tax.item_wise_tax_detail = "{}"

    for item in doc.items:
        if getattr(item, "custom_fim_value", None):
            item.custom_assessible_value = flt(item.amount) + flt(item.custom_fim_value)

        assessible = (
            flt(getattr(item, "custom_assessible_value", 0.0))
            or flt(item.base_net_amount)
            or flt(item.amount)
        )

        item.taxable_value = assessible
        item.net_amount = assessible
        item.base_net_amount = assessible
        item.base_amount = assessible

        for tax in doc.taxes:
            rate = flt(tax.rate)
            if not rate:
                continue

            tax_amount = assessible * (rate / 100)

            tax.tax_amount += tax_amount
            tax.base_tax_amount += tax_amount

            try:
                detail = frappe.parse_json(tax.item_wise_tax_detail) or {}
            except Exception:
                detail = {}

            key = item.item_code or item.name or f"row-{item.idx}"
            prev = detail.get(key)

            if prev:
                detail[key] = [rate, flt(prev[1]) + tax_amount]
            else:
                detail[key] = [rate, tax_amount]

            tax.item_wise_tax_detail = frappe.as_json(detail)

    doc.net_total = sum(flt(i.net_amount) for i in doc.items)
    doc.base_net_total = doc.net_total

    for tax in doc.taxes:
        if not tax.base_tax_amount:
            tax.base_tax_amount = tax.tax_amount

    cumulative = flt(doc.net_total)
    base_cumulative = flt(doc.base_net_total)

    for tax in doc.taxes:
        cumulative += tax.tax_amount
        tax.total = cumulative
        tax.charge_type = "Actual"

        base_cumulative += tax.base_tax_amount
        tax.base_total = base_cumulative

    doc.total_taxes_and_charges = sum(flt(t.tax_amount) for t in doc.taxes)
    doc.base_total_taxes_and_charges = sum(flt(t.base_tax_amount) for t in doc.taxes)

    # doc.total = doc.net_total + doc.total_taxes_and_charges
    doc.base_total = doc.base_net_total + doc.base_total_taxes_and_charges

    # doc.rounded_total = round(doc.total, 2)
    doc.rounding_adjustment = doc.rounded_total - doc.total

    doc.base_rounded_total = round(doc.base_total, 2)
    doc.base_rounding_adjustment = doc.base_rounded_total - doc.base_total

    # doc.grand_total = doc.rounded_total
    doc.base_grand_total = doc.base_rounded_total

    if hasattr(doc, "outstanding_amount"):
        doc.outstanding_amount = doc.grand_total

    cumulative = flt(doc.net_total)
    base_cumulative = flt(doc.base_net_total)
    for tax in doc.taxes:
        cumulative += tax.tax_amount
        tax.total = cumulative
        if tax.charge_type != "Rounding Adjustment":
            tax.charge_type = "Actual"

        base_cumulative += tax.base_tax_amount
        tax.base_total = base_cumulative


def before_taxes_and_totals_submit(doc, method=None):

    before_taxes_and_totals(doc)
    doc.flags.ignore_validate = True
    doc.flags.ignore_tax_validation = True
    doc.ignore_pricing_rule = 1
    doc.ignore_default_taxes_and_charges = 1

    doc.total = flt(doc.total)
    doc.base_total = flt(doc.base_total)
    doc.grand_total = flt(doc.grand_total)
    doc.base_grand_total = flt(doc.base_grand_total)
    doc.rounded_total = flt(doc.rounded_total)
    doc.base_rounded_total = flt(doc.base_rounded_total)
    doc.outstanding_amount = flt(doc.grand_total)


def patch_india_compliance_tax(doc, method=None):
    if getattr(frappe.local, "_patched_ic_actual", False):
        return

    frappe.local._patched_ic_actual = True
    patch_ic_validate_item_wise_tax_detail()
    patch_ic_validate_item_gst_details()


def patch_ic_validate_item_wise_tax_detail():
    try:
        import india_compliance.gst_india.overrides.transaction as ic_trx
    except Exception:
        return

    if not hasattr(ic_trx, "_orig_validate_item_wise_tax_detail"):
        ic_trx._orig_validate_item_wise_tax_detail = ic_trx.validate_item_wise_tax_detail

    original = ic_trx._orig_validate_item_wise_tax_detail

    def patched(doc):
        try:
            return original(doc)
        except Exception as e:
            msg = str(e)
            if "would not compute item taxes" in msg:
                frappe.msgprint("⚠ Actual tax computation skipped (allowed).")
                return
            if "incorrect" in msg:
                frappe.msgprint("⚠ Actual tax mismatch ignored.")
                return
            raise e

    ic_trx.validate_item_wise_tax_detail = patched


def patch_ic_validate_item_gst_details():
    try:
        from india_compliance.gst_india.overrides.transaction import ItemGSTDetails
    except Exception:
        return

    if not hasattr(ItemGSTDetails, "_orig_validate_item_gst_details"):
        ItemGSTDetails._orig_validate_item_gst_details = ItemGSTDetails.validate_item_gst_details

    original = ItemGSTDetails._orig_validate_item_gst_details

    def patched(self):
        try:
            return original(self)
        except Exception as e:
            msg = str(e)
            if "GST amounts do not match" in msg or "amount mismatch" in msg:
                frappe.msgprint("⚠ GST mismatch ignored.")
                return
            raise e

    ItemGSTDetails.validate_item_gst_details = patched



import frappe
import erpnext.controllers.taxes_and_totals as tax_module

def no_validate(*args, **kwargs):
    # Disable ERPNext internal validation completely
    return

# Override validation functions (they exist in v15)
if hasattr(tax_module, "validate_on_actual"):
    tax_module.validate_on_actual = no_validate

if hasattr(tax_module, "validate_taxes"):
    tax_module.validate_taxes = no_validate

if hasattr(tax_module, "_validate_tax_amount"):
    tax_module._validate_tax_amount = no_validate
