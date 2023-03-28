from odoo import fields, models, api, _
import locale
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
import pytz

#locale.setlocale(locale.LC_ALL, 'en_US')

def hour_rounder(t):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    return (t.replace(second=0, microsecond=0, minute=0, hour=t.hour))


class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'
    _order = 'date_start desc, barcode asc'

    pin = fields.Char(string="NIK", related='employee_id.pin', store=True)
    barcode = fields.Char(string="Old NIK", related='employee_id.barcode', store=True)
    pay_status = fields.Selection(string='Employee Status', related='employee_id.status', store=True)
    empl_active = fields.Boolean(string='Active Employee', related='employee_id.active')
    empl_group_id = fields.Many2one('employee.group', string='Group', related='employee_id.hr_group_id', store=True)
    empl_department = fields.Many2one('hr.department', string='Dept', related='employee_id.department_id', store=True)
    pay_location = fields.Many2one('pay.location', string='Pay Loc', related='employee_id.pay_location', store=True)
    pay_group = fields.Many2one('pay.group', string='Pay Group', related='employee_id.pay_group', store=True)
    pay_department = fields.Many2one('pay.department', string='Pay Dept', related='employee_id.pay_department', store=True)
    actual_date = fields.Char(string='Tanggal', compute='_get_separate_date', store=True)
    masuk = fields.Char(string='Masuk', compute='_get_separate_date', store=True)
    keluar = fields.Char(string='Keluar', compute='_get_separate_date', store=True)
    sched_in = fields.Char(string='Sched In', compute='_get_separate_date', store=True)
    sched_out = fields.Char(string='Sched Out', compute='_get_separate_date', store=True)
    actual_in = fields.Datetime(string='Actual In')
    actual_out = fields.Datetime(string='Actual Out')
    duration = fields.Float(compute='_compute_duration', store=True, string="Work Hours", readonly=False)
    add_break = fields.Float(string="Break time",digits=(10,1))
    day = fields.Char(string="Day", compute="_compute_duration",store=True, readonly=False)
    paid = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Paid")
    is_paid = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Paid', compute='_get_paid', store=True)
    note = fields.Char(string="Note")
    attendance_ids = fields.One2many('hr.attendance', 'entry_id',string="Attendances")
    old_we_type_id = fields.Many2one('hr.work.entry.type', string="Old WE")

    _sql_constraints = [
        ('_work_entry_has_end', 'check (date_stop IS NOT NULL)',
         'Work entry must end. Please define an end date or a duration.'),
        ('_work_entry_start_before_end', 'Check(1=1)', 'Starting time should be before end time.')
    ]

    def write(self, vals):
        if vals.get('work_entry_type_id'):
            if vals.get('work_entry_type_id'):
                vals['old_we_type_id'] = vals.get('work_entry_type_id')
        res = super(HrWorkEntry, self).write(vals)
        return res

    def action_view_detail(self):
        self.ensure_one()
        action = self.env.ref("akm_attendances.fd_attendances_action")
        result = action.read()[0]
        attend = self.env['fd.attendances']
        # if self.actual_out:
        #     actual_in = self.actual_in - relativedelta(days=1)
        #     actual_out = self.actual_out + relativedelta(days=1)
        #     attend = self.env['fd.attendances'].search([('punch_time','>=',actual_in),
        #                                                ('punch_time','<=',actual_out),
        #                                                ('name','=',self.employee_id.id)])
        # else:
        actual_in = self.date_start.replace(hour=0) - timedelta(days=1)
        actual_out = self.date_start.replace(hour=0) + relativedelta(days=2)
        attend = self.env['fd.attendances'].search([('punch_time', '>=', actual_in),
                                                   ('punch_time', '<=', actual_out),
                                                   ('name', '=', self.employee_id.id)])
                                                   
        result["domain"] = [("id", "in", attend.ids)]
        return result

    @api.depends('work_entry_type_id','work_entry_type_id.is_leave')
    def _get_paid(self):
        for x in self:
            flg = x.work_entry_type_id.is_leave or False
            if flg:
                x.is_paid = 'no'
            else:
                x.is_paid = 'yes'

    @api.depends('actual_in','actual_out','date_start', 'date_stop')
    def _get_separate_date(self):
        for we in self:
            dayin = we.date_start.astimezone(pytz.timezone('Asia/Jakarta'))
            actual_date = dayin.date() or False
            if actual_date:
                we.actual_date = actual_date.strftime("%d-%m-%Y")
            else:
                we.actual_date = '-'
            we.masuk = self._susun_time(we.actual_in)
            we.keluar = self._susun_time(we.actual_out)
            we.sched_in = self._susun_time(we.date_start)
            we.sched_out = self._susun_time(we.date_stop)
            if we.date_start < datetime.strptime('2022-10-01','%Y-%m-%d'):
                cek=0
            day = self._convert_day_indo(dayin.strftime('%A'))
            we.day = day

    def _susun_time(self, time):
        a = time.astimezone(pytz.timezone('Asia/Jakarta')).time() if time else 0
        if a:
            hour = str(a.hour).zfill(2)
            minu = str(a.minute).zfill(2)
            sec = str(a.second).zfill(2)
            rangkai = hour+":"+minu+":"+sec
            return rangkai
        else:
            return ""

    @api.model
    def refresh_separate_date(self, dfrom=None,dto=None,mode=None):
        domain=[]
        if dfrom:
            domain.append(('date_start','>=',dfrom))
        if dto:
            domain.append(('date_stop','<=',dto))
        res = self.env['hr.work.entry'].search(domain)

        if not mode or mode=='A':
            res._get_separate_date()
        if not mode or mode == 'B':
            res._compute_duration()

    @api.depends('actual_in', 'actual_out','date_start','add_break')
    def _compute_duration(self):
        att_obj = self.env['hr.attendance']
        for we in self:
            calendar= we.employee_id.resource_calendar_id
            if we.actual_in and we.actual_out:
                if self.env.company.use_calendar:
                    wh = calendar.get_work_duration_simple(we.actual_in, we.actual_out)
                    we.duration = wh['hours']
                    # if we.add_break>0 and we.add_break<we.duration:
                    #     we.duration -= we.add_break
                else:
                    wh = att_obj._get_work_hours_basic(we.actual_in, we.actual_out)
                    we.duration = wh
                    # if we.add_break>0 and we.add_break<we.duration:
                    #     we.duration -= we.add_break
            else:
                we.duration = 0
                # we.add_break = 0

    def _convert_day_indo(self, dayin):
        if dayin=='Sunday': res = 'Minggu'
        elif dayin == 'Monday': res = 'Senin'
        elif dayin == 'Tuesday': res = 'Selasa'
        elif dayin == 'Wednesday': res = 'Rabu'
        elif dayin == 'Thursday': res = 'Kamis'
        elif dayin == 'Friday': res = 'Jumat'
        elif dayin == 'Saturday': res = 'Sabtu'
        else: res = ""
        return res

    @api.depends('duration')
    def _compute_date_stop(self):
        return 0
            # work_entry.actual_out = work_entry.actual_in + relativedelta(hours=work_entry.duration)

class HrWorkEntryType(models.Model):
    _inherit = 'hr.work.entry.type'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """ search full name and barcode """
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    def name_get(self):
        result = []
        for rewrite in self:
            name = rewrite.name
            if rewrite.code:
                name = rewrite.code
            result.append((rewrite.id, name))
        return result
