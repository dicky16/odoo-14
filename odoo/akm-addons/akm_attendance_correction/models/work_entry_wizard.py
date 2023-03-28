from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class HrWorkEntryRegenerationWizard(models.TransientModel):
    _inherit = 'hr.work.entry.regeneration.wizard'

    employee_ids = fields.Many2many('hr.employee', 'employee_entry_rel', 'entry_id', 'emp_id', string='Employees')
    employee_id = fields.Many2one('hr.employee', 'Employee')

    @api.onchange('employee_ids')
    def _onchange_employee(self):
        if self.employee_ids:
            self.employee_id = self.employee_ids[0].id.origin
        else:
            self.employee_id = False

    def regenerate_work_entries(self):
        if not self.employee_ids or not self.date_from or not self.date_to:
            return ValidationError(_("In order to regenerate the work entries, you need to provide the wizard with an employee_id, a date_from and a date_to. In addition to that, the time interval defined by date_from and date_to must not contain any validated work entries."))
        for emp in self.employee_ids:
            self._sub_regenerate_entries(emp, self.date_from, self.date_to)

    @api.model
    def generate_auto_we(self, nik=None):
        empdom = [('active', '=', True), ('contract_id', '!=', False)]
        if nik:
            empdom += [('nik','=',nik)]
        employee_ids = self.env['hr.employee'].search(empdom)
        dfrom = fields.Date.today() - relativedelta(days=1)
        dto = dfrom

        if len(employee_ids)==0 or not dfrom or not dto:
            print('In order to regenerate the work entries, you need to provide the wizard with an employee_id, a date_from and a date_to. In addition to that, the time interval defined by date_from and date_to must not contain any validated work entries.')
            # return ValidationError(_("In order to regenerate the work entries, you need to provide the wizard with an employee_id, a date_from and a date_to. In addition to that, the time interval defined by date_from and date_to must not contain any validated work entries."))
        for emp in employee_ids:
            self._sub_regenerate_entries(employee=emp, date_from=dfrom, date_to=dto, force=True)

    def _sub_regenerate_entries(self, employee, date_from, date_to, force=False):
        # self.ensure_one()
        if not self.valid and not force:
            raise ValidationError(_("In order to regenerate the work entries, you need to provide the wizard with an employee_id, a date_from and a date_to. In addition to that, the time interval defined by date_from and date_to must not contain any validated work entries."))
        #
        self._clear_old_entries(employee,date_from, date_to)
        employee.with_context(force_work_entry_generation=True).generate_work_entries(date_from, date_to)
        action = self.env.ref('hr_work_entry.hr_work_entry_action').sudo().read()[0]
        return action

    def _clear_old_entries(self, employee, dfrom, dto):
        work_entries = self.env['hr.work.entry'].search([('employee_id', '=', employee.id),
                                                         ('date_stop', '>=', dfrom),
                                                         ('date_start', '<=', dto)])
        work_entries.write({'active': False})