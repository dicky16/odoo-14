from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class HrWorkEntryRegenerationWizard(models.TransientModel):
    _inherit = 'hr.work.entry.regeneration.wizard'

    def _clear_old_entries(self, employee, dfrom, dto):
        work_entries = self.env['hr.work.entry'].search([('employee_id', '=', employee.id),
                                                         ('date_stop', '>=', dfrom),
                                                         ('date_start', '<=', dto),
                                                         ('overtime_line_ids','=',False),
                                                         ('old_we_type_id','=',False)])
        work_entries.write({'active': False})