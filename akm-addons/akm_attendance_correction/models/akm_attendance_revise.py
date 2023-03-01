from odoo import models, fields, api, _
from datetime import datetime, time, timedelta
import pytz

def hour_rounder(t):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    return (t.replace(second=0, microsecond=0, minute=0, hour=t.hour))

class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    entry_id = fields.Many2one('hr.work.entry', string='Entries')
    pay_status = fields.Selection(string='Employee Status', related='employee_id.status', store=True)
    notes = fields.Char(string='Note')
    worked_hours = fields.Float(string='Worked Hours', compute='_compute_worked_hours', store=True, readonly=True, digits=(10,1))

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                check_in = attendance.check_in.replace(tzinfo=pytz.utc)
                check_out = attendance.check_out.replace(tzinfo=pytz.utc)
                attendance.worked_hours = attendance._get_work_hours(check_in, check_out)
            else:
                attendance.worked_hours = False

    @api.model
    def calc_all_wh(self, from_date=None, to_date=None, cek_err=None):
        domain = []
        if from_date:
            domain.append(('check_in','>=',from_date))
        if to_date:
            domain.append(('check_in','<=',to_date))
        if cek_err:
            domain.append(('worked_hours', '>', cek_err))
        res = self.env['hr.attendance'].search(domain, order='check_in asc')
        res.action_get()
        return
        
    def action_get(self):
        for x in self:
            wh = 0
            if x.check_in and x.check_out and x.employee_id.resource_calendar_id:
                if x.check_out and x.check_in:
                    check_in = x.check_in.replace(tzinfo=pytz.utc)
                    check_out = x.check_out.replace(tzinfo=pytz.utc)
                    wh = x._get_work_hours(check_in, check_out) or 0

            x.worked_hours = wh

    def action_view_detail(self):
        self.ensure_one()
        action = self.env.ref("akm_attendances.fd_attendances_action")
        result = action.read()[0]
        result["domain"] = [("attend_id", "=", self.id)]
        return result

    def _get_work_hours(self, check_in, check_out):
        if self.env.company.use_calendar:
            wh = self.employee_id.resource_calendar_id.get_work_duration_simple(check_in, check_out)
            return wh['hours'] # Options = hours, rests, interval
        else:
            wh = self._get_work_hours_basic(check_in, check_out)
            return wh

    def _get_work_hours_old(self, check_in, check_out):
        tz = pytz.timezone(self._context.get('tz', 'utc') or 'utc')
        if check_in-hour_rounder(check_in) < timedelta(minutes=1):
            check_in = hour_rounder(check_in)
        else:
            check_in = hour_rounder(check_in) + timedelta(hours=1)
        check_out = hour_rounder(check_out)
        start = check_in.astimezone(tz)
        stop = check_out.astimezone(tz)
        if stop>stop.replace(second=0, microsecond=0, minute=0, hour=12):
            to_check = stop
        else:
            to_check = start
        day = str(int(to_check.strftime('%w'))-1)
        calendar = self.employee_id.resource_calendar_id or self.env.company.calendar_id or False
        if not calendar:
            return 0
        else:
            atten = self.env['resource.calendar.attendance'].search([('calendar_id','=',calendar.id),
                                                                     ('dayofweek','=',day)], limit=1)
            if atten:
                rest = timedelta(hours=atten.rest_time) if (stop-start).total_seconds() / 3600 > 5 else timedelta(hours=0)
                tengahan = start.replace(second=0, microsecond=0, minute=0, hour=12)
                if start < tengahan and stop > tengahan and atten.dayofweek=="4":
                    rest = timedelta(hours=1.5)
                elif rest:
                    rest = timedelta(hours=1)

            else:
                tengahan = stop.replace(second=0, microsecond=0, minute=0, hour=12)
                hari = start.strftime("%A")
                if start < tengahan and stop>tengahan and hari=="Friday":
                    rest = timedelta(hours=1.5)
                else:
                    rest = timedelta(hours=1)
            workhour = (stop-start-rest).total_seconds() / 3600
            if workhour<0:
                workhour = 0
            return workhour

    def _get_work_hours_basic(self, check_in, check_out):
        tz = pytz.timezone(self._context.get('tz', 'utc') or 'utc')
        # CI round up, CO round down
        if check_in-hour_rounder(check_in) < timedelta(minutes=1):
            check_in = hour_rounder(check_in)
        else:
            check_in = hour_rounder(check_in) + timedelta(hours=1)
        check_out = hour_rounder(check_out)
        start = check_in.astimezone(tz)
        stop = check_out.astimezone(tz)
        wh_gross = stop-start

        day = str(int(start.strftime('%w'))-1)
        if int(day)<0: day = 6
        calendar = self.env.company.calendar_id or False
        if not calendar:
            return 0
        else:
            atten = self.env['resource.calendar.attendance'].search([('calendar_id','=',calendar.id),
                                                                     ('dayofweek','=',day)], limit=1)
            if atten:
                ci_dom = self._get_domain(start, atten)
                co_dom = self._get_domain(stop, atten)
                if ci_dom in ['A','B'] and co_dom in ['C', 'D']:
                    rest = timedelta(hours=atten.rest_time)
                else:
                    if ci_dom in ['C','D'] and wh_gross>timedelta(hours=5):
                        rest = timedelta(hours=1)
                    else:
                        rest = timedelta(hours=0)
            else:
                if wh_gross.total_seconds()/3600>5:
                    rest = timedelta(hours=1)
                else:
                    rest = timedelta(hours=0)
            resu = wh_gross-rest
            result = resu.total_seconds()/3600
            if result<0:
                result=0
            return result

    def _get_domain(self,time, atten):
        base = time.replace(hour=0, minute=0,second=0)
        if time <= base+timedelta(atten.hour_from/24):
            domain = "A"
        elif time > base+timedelta(atten.hour_from/24) and time <= base+timedelta(hours=atten.rest_start, minutes=7):
            domain = "B"
        elif time > base+timedelta(atten.rest_start/24) and time <= base+timedelta(atten.hour_to/24):
            domain = "C"
        else:
            domain = "D"
        return domain
