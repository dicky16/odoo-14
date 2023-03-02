# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression

class DisciplinaryStage(models.Model):
    _name='disciplinary.stage'
    _rec_name='disciplinary_name'

    disciplinary_name=fields.Char(String="Name", required=True)
    disciplinary_code=fields.Char(String="Code", required=True)
    disciplinary_stage=fields.Integer(String="Stage", required=True)
    valid_for_months=fields.Integer(String="Valid for (months)")
    after_x_days=fields.Integer(String="After", required=True, default=1)
    # manual_action=fields.Boolean(String="Manual Action")
    send_email=fields.Boolean(String="Send an Email")
    send_letter=fields.Boolean(String="Send a Letter")
    # assign_a_responsible=fields.Many2one('hr.employee', String="Assign a Responsible")
    # action_to_do=fields.Text()
    letter_content=fields.Html(translate=True)
    sequence=fields.Integer(String="Sequence", related="disciplinary_stage")


    def name_get(self):
        res = []
        for rec in self:
            name = rec.disciplinary_name
            if rec.disciplinary_code:
                name = '[' + rec.disciplinary_code + '] ' + name
            res.append((rec.id, name))
        return res

class DisciplinaryHistory(models.Model):
    _name = 'disciplinary.history'

    date_diciplined = fields.Date('Date Disciplined')
    disciplinary_stage = fields.Many2one('disciplinary.stage')
    valid_until = fields.Date()
    reason_disciplinary=fields.Text(string="Reason of Disciplinary", required=True)
    manual_action=fields.Text(string="Action Taken")
    employee_id = fields.Many2one('hr.employee')
    employee_barcode = fields.Char(string="Old NIK", related='employee_id.barcode')
    employee_pin = fields.Char(string="NIK", related='employee_id.pin')
    employee_pay_department = fields.Many2one('pay.department', string="Pay Department", related='employee_id.pay_department')
    employee_pay_group = fields.Many2one('pay.group', string="Pay Group", related='employee_id.pay_group')
    employee_pay_location = fields.Many2one('pay.location', string="Pay Location", related='employee_id.pay_location')
    attachment = fields.Binary('Attachment')
    attachment_name = fields.Char()
    disciplinary_document = fields.Binary('Document')

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    disciplinary_history_ids = fields.One2many('disciplinary.history', 'employee_id')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """ search full name and barcode """
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        elif operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = [('name', operator, name), ('pin', operator, name), ('barcode', operator, name)]
        else:
            domain = ['|','|', ('name', operator, name), ('pin', operator, name), ('barcode', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
