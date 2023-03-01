# -*- coding: utf-8 -*-
import base64
import datetime

from datetime import timedelta
from odoo import models, fields, api,_
from odoo.exceptions import Warning

class DisciplinaryWizard(models.TransientModel):
    _name = 'disciplinary.wizard'

    employee=fields.Many2one('hr.employee', string="Employee", required=True)
    employee_nik = fields.Char(String='NIK', related='employee.pin')
    employee_nik_old = fields.Char(String='Old NIK', related='employee.barcode')
    employee_pay_department = fields.Many2one('pay.department', string="Pay Department", related='employee.pay_department')
    employee_pay_group = fields.Many2one('pay.group', string="Pay Group", related='employee.pay_group')
    employee_pay_location = fields.Many2one('pay.location', string="Pay Location", related='employee.pay_location')
    disciplined_date=fields.Date(string="Disciplined Date", required=True)
    disciplinary_stages=fields.Many2one('disciplinary.stage', string="Disciplinary Stages", required=True)
    valid_for_months=fields.Integer(string="Valid for (Months)", related="disciplinary_stages.valid_for_months")
    reason_disciplinary=fields.Text(string="Reason of Disciplinary", required=True)
    # manual_action=fields.Text(string="Manual Action", related="disciplinary_stages.action_to_do")
    send_an_email=fields.Boolean(string="Sent an Email", related="disciplinary_stages.send_email")
    send_a_letter=fields.Boolean(string="Sent a Letter", related="disciplinary_stages.send_letter")
    letter_content = fields.Html()
    document = fields.Binary(String="Document")
 
    # @api.multi
    def allocate_disciplinary(self):
        for obj in self:
            # import pdb; pdb.set_trace()
            for history in obj.employee.disciplinary_history_ids:
                if history.disciplinary_stage == obj.disciplinary_stages:
                    raise Warning("Selected Employee already has " + str(obj.disciplinary_stages.disciplinary_name)+'.')

            if obj.valid_for_months>0:
                date = (datetime.date.today() + datetime.timedelta(obj.valid_for_months*365/12)).isoformat()
            else:
                date = False

            vals = {
                "date_diciplined": obj.disciplined_date,
                "disciplinary_stage": obj.disciplinary_stages.id,
                "valid_until": date,
                "reason_disciplinary": obj.reason_disciplinary,
                # "manual_action" : obj.manual_action,
                "employee_id": obj.employee.id,
                "disciplinary_document": obj.document,
            }

            self.employee.write({'disciplinary_history_ids': [(0,0, vals)]})

            return {
                'name': _('History'),
                'view_mode': 'tree,form',
                'res_model': 'disciplinary.history',
                'view_id': False,
                # 'views': [(self.env.ref('account.view_account_payment_tree').id, 'tree'),
                #           (self.env.ref('account.view_account_payment_form').id, 'form')],
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', [x.id for x in self.employee.disciplinary_history_ids])],
                'context': {'create': False},
            }
