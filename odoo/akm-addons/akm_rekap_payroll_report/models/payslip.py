from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from odoo.exceptions import UserError

class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    payslip_run_id = fields.Many2one('hr.payslip.run', related='payslip_id.payslip_run_id', store=True)
    is_positive = fields.Boolean(string='Positive', related='input_type_id.is_positive', store=True)

class HrPayslipInputType(models.Model):
    _inherit = 'hr.payslip.input.type'

    is_positive = fields.Boolean(string='Positive')