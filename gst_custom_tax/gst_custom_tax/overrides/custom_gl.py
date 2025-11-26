# import frappe
# from frappe.utils import flt
# from erpnext.accounts.general_ledger import make_gl_entries
# # Store original reference
# from erpnext.accounts.general_ledger import make_gl_entries as _original_make_gl_entries


# def custom_make_gl_entries(gl_map, adv_adj, update_outstanding, from_repost=False):

#     frappe.throw("kk")
#     """
#     Override GL generation so it uses custom taxable values.
#     This prevents Debit/Credit mismatch.
#     """

#     for row in gl_map:
#         # If linked to a Sales Invoice Item
#         if row.get("voucher_detail_no"):
#             item = frappe.get_doc("Sales Invoice Item", row["voucher_detail_no"])

#             assessible = (
#                 flt(getattr(item, "custom_assessible_value", 0))
#                 or flt(item.net_amount)
#                 or flt(item.amount)
#             )

#             # Replace debit/credit base with assessible value
#             if row.debit:
#                 row.debit = assessible
#             if row.credit:
#                 row.credit = assessible

#     # now call ERPNext original GL handler
#     return _original_make_gl_entries(gl_map, adv_adj, update_outstanding, from_repost)
