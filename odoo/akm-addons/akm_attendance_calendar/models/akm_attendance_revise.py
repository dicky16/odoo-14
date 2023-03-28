from odoo import models, fields, api, _
from datetime import datetime, time, timedelta
import pytz

def hour_rounder(t):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    return (t.replace(second=0, microsecond=0, minute=0, hour=t.hour))

class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    pay_status = fields.Selection(string='Employee Status', related='employee_id.status', store=True)
    notes = fields.Char(string='Note')
    worked_hours = fields.Float(string='Worked Hours', compute='_compute_worked_hours', store=True, readonly=True)

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                check_in = attendance.check_in.replace(tzinfo=pytz.utc)
                check_out = attendance.check_out.replace(tzinfo=pytz.utc)
                attendance.worked_hours = attendance._get_work_hours(check_in, check_out)
            else:
                attendance.worked_hours = False

    def action_get(self):
        for x in self:
            wh = 0
            if x.check_in and x.check_out and x.employee_id.resource_calendar_id:
                if x.check_out and x.check_in:
                    check_in = x.check_in.replace(tzinfo=pytz.utc)
                    check_out = x.check_out.replace(tzinfo=pytz.utc)
                    wh = x._get_work_hours(check_in, check_out)

            x.worked_hours = wh

    def _get_work_hours(self, check_in, check_out):
        tz = pytz.timezone(self._context.get('tz', 'utc') or 'utc')
        if self.env.company.use_calendar:
            wh = self.employee_id.resource_calendar_id.get_work_duration_simple(check_in, check_out)
            return wh['hours'] # Options = hours, rests, interval
        else:
            check_in = hour_rounder(check_in) + timedelta(hours=1)
            check_out = hour_rounder(check_out)
            start = check_in.astimezone(tz)
            stop = check_out.astimezone(tz)
            day = str(int(stop.strftime('%w'))-1)
            calendar = self.employee_id.resource_calendar_id or self.env.company.calendar_id or False
            if not calendar:
                return 0
            else:
                atten = self.env['resource.calendar.attendance'].search([('calendar_id','=',calendar.id),
                                                                         ('dayofweek','=',day)], limit=1)
                if atten:
                    rest = timedelta(hours=atten.rest_time) if (stop-start).total_seconds() / 3600 > 5 else timedelta(hours=0)
                else:
                    rest = 0
                workhour = (stop-start-rest).total_seconds() / 3600
                return workhour