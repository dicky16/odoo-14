from odoo import fields, models, api, _
import locale
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
import pytz

#locale.setlocale(locale.LC_ALL, 'en_US')

class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    overtime_count = fields.Integer('#Overtime', compute='_compute_overtime_count', store=True)
    overtime_line_ids = fields.One2many('overtime.request.line', 'entries_id', string='Overtime')

    def name_get(self):
        res = []
        for rec in self:
            name = "%s" % (rec.sched_in)
            if rec.work_entry_type_id:
                name += "(%s)" % (rec.work_entry_type_id.name)
            res += [(rec.id, name)]
        return res

    @api.depends('date_start','employee_id','overtime_line_ids')
    def _compute_overtime_count(self):
        for x in self:
            line = self.env['overtime.request.line'].search([('request_date','=',x.date_start.date()),
                                                   ('employee_id','=',x.employee_id.id)])
            if len(line):
                x.overtime_count = len(line)
            else:
                x.overtime_count = 0

    def action_view_overtime(self):
        self.ensure_one()
        action = self.env.ref("akm_overtime.action_overtime_request_summary")
        result = action.read()[0]
        line = self.env['overtime.request.line'].search([('request_date','=',self.date_start.date()),
                                               ('employee_id','=',self.employee_id.id)])
        if line:
            result["domain"] = [("id", "in", line.overtime_id.ids)]
        return result