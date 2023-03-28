from odoo import api, fields, models,_
from odoo.exceptions import ValidationError

class HrEmployeePrivate(models.Model):
    _inherit = "hr.employee"


    @api.depends('resource_id.active')
    def _depend_active(self):
        for emp in self:
            x = emp.resource_id.active
            raise ValidationError("test")