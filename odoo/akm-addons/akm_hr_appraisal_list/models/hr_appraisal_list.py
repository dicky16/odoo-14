from odoo import models, fields, api

class HrAppraisal(models.Model):
    _inherit = 'hr.appraisal'

    periode2 = fields.Char(string='Masa Kerja', store=True, related="employee_id.periode2")