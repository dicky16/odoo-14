from odoo import fields, models, api

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    currency_id = fields.Many2one(related='contract_id.currency_id')
    wage = fields.Monetary(string="Wage", related="contract_id.wage")
    hourly_wage = fields.Monetary(string="Hourly Wage", related="contract_id.hourly_wage")
 
class ConfirmationEmployee(models.TransientModel):
    _name = 'confirmation.employee'

    def confirm_yes(self):
        self.env['hr.employee'].get_employees()

    def cancel_button(self):
        return {
            'type': 'ir.actions.act_window_close'
        }
