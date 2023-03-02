from odoo import fields, models, api, _


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    pin = fields.Char(string="NIK", related="user_id.pin", readonly=True)
    barcode = fields.Char(string="Old NIK", related="user_id.barcode", readonly=True)
    identification_id = fields.Char(string="KTP", related="user_id.identification_id", readonly=True)
