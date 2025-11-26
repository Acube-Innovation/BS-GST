# import frappe
# from frappe.utils import cint
# # import the original module
# import erpnext.controllers.accounts_controller as acc_ctrl


# def custom_validate_taxes_and_charges(tax):
    
  
    
#     if tax.charge_type in ["Actual", "On Net Total", "On Paid Amount"] and tax.row_id:
#         frappe.throw(
#             ("Can refer row only if the charge type is 'On Previous Row Amount' or 'Previous Row Total'")
#         )

#     elif tax.charge_type in ["On Previous Row Amount", "On Previous Row Total"]:
#         if cint(tax.idx) == 1:
#             frappe.throw(
#                 ("Cannot select charge type as 'On Previous Row Amount' or 'On Previous Row Total' for first row")
#             )
#         elif not tax.row_id:
#             frappe.throw(
#                 ("Please specify a valid Row ID for row {0} in table {1}").format(
#                     tax.idx, (tax.doctype)
#                 )
#             )
#         elif tax.row_id and cint(tax.row_id) >= cint(tax.idx):
#             frappe.throw(
#                 ("Cannot refer row number greater than or equal to current row number for this Charge type")
#             )


# import india_compliance.gst_india.overrides.transaction as ic_txn

# def disable_validate_item_wise_tax_detail(*args, **kwargs):
#     # Completely skip India Compliance GST validation
#     return

# # Patch the function safely
# if hasattr(ic_txn, "validate_item_wise_tax_detail"):
#     ic_txn.validate_item_wise_tax_detail = disable_validate_item_wise_tax_detail
import frappe
from frappe.utils import cint

# ---------------------------
# Override ERPNext's validate_taxes_and_charges
# ---------------------------

import erpnext.controllers.accounts_controller as acc_ctrl

def custom_validate_taxes_and_charges(tax):

    if tax.charge_type in ["Actual", "On Net Total", "On Paid Amount"] and tax.row_id:
        frappe.throw(
            ("Can refer row only if the charge type is 'On Previous Row Amount' or 'Previous Row Total'")
        )

    elif tax.charge_type in ["On Previous Row Amount", "On Previous Row Total"]:
        if cint(tax.idx) == 1:
            frappe.throw(
                ("Cannot select charge type as 'On Previous Row Amount' or 'On Previous Row Total' for first row")
            )
        elif not tax.row_id:
            frappe.throw(
                ("Please specify a valid Row ID for row {0} in table {1}").format(
                    tax.idx, (tax.doctype)
                )
            )
        elif tax.row_id and cint(tax.row_id) >= cint(tax.idx):
            frappe.throw(
                ("Cannot refer row number greater than or equal to current row number for this Charge type")
            )

# Patch ERPNext controller
acc_ctrl.validate_taxes_and_charges = custom_validate_taxes_and_charges


# ---------------------------
# Disable India Compliance GST validation
# ---------------------------

import india_compliance.gst_india.overrides.transaction as ic_txn

def disable_validate_item_wise_tax_detail(*args, **kwargs):
    # Skip GST validation entirely
    return

# Patch the validation
if hasattr(ic_txn, "validate_item_wise_tax_detail"):
    ic_txn.validate_item_wise_tax_detail = disable_validate_item_wise_tax_detail
