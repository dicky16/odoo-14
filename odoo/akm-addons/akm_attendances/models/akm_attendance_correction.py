from odoo import fields, models, api, _
import locale
from datetime import datetime, timedelta, date
from pytz import timezone, UTC, utc


class AttendanceCorrection(models.Model):
    _name = 'attendance.correction'

    pin = fields.Char(string="NIK", compute="_compute_pin")
    barcode = fields.Char(string="Old NIK", readonly="1")
    name = fields.Many2one('hr.employee', string="Nama")
    pay_group = fields.Many2one('pay.group', string='Group', readonly="1")
    pay_department = fields.Many2one('pay.department', string='Dept', readonly="1")
    tanggal = fields.Date(string="Tanggal", readonly="1")
    schedule_in = fields.Char(string="Schedule In", readonly="1")
    schedule_out = fields.Char(string="Schedule Out", readonly="1")
    check_in = fields.Char(string="Masuk", readonly="1")
    check_out = fields.Char(string="Keluar", readonly="1")
    worked_hours = fields.Float(string="Tot Work", readonly="1")
    flag_sts = fields.Selection([('m', 'M'), ('i', 'I'), ('a', 'A')], string="Flag Sts")
    hari = fields.Char(string="Hari", compute="_compute_day")
    paid = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Paid", compute="_compute_paid")
    note = fields.Char(string="Note")
    attendance_id = fields.Integer(string="Hr Attendance ID")

    @api.depends("name")
    def _compute_pin(self):
        for record in self:
            record.pin = record.name.pin
            record.barcode = record.name.barcode
            record.pay_group = record.name.pay_group
            record.pay_department = record.name.pay_department
            calendar_id = record.name.resource_calendar_id.id
            dayofweek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day = dayofweek.index(record.hari)
            data = self.env['resource.calendar.attendance'].search([
                ('calendar_id', '=', calendar_id),
                ('dayofweek', '=', str(day))
            ])
            record.schedule_in = data[0].hour_from
            record.schedule_out = data[0].hour_to

    @api.depends("tanggal")
    def _compute_day(self):
        for record in self:
            record.hari = record.tanggal.strftime("%A") if record.tanggal else "Sunday"
            record.flag_sts = "m" if record.check_in and record.check_out else "a"

    @api.onchange("check_in", "check_out")
    def onchange_attendance(self):
        for record in self:
            record.flag_sts = "m" if record.check_in and record.check_out else "a"

    @api.depends("flag_sts")
    def _compute_paid(self):
        for record in self:
            record.paid = "yes" if record.flag_sts == "m" else "no"

    def copy_attendances(self):
        day = 2
        scrape_attendances = []
        for i in range(day):
            now = date.today() - timedelta(days=day)
            attendances = self.env['hr.attendance'].search([('date_fd', '=', now)], order="id asc")
            scrape_attendances.extend(attendances)
            day -= 1

        for i in scrape_attendances:
            check_data = self.env['attendance.correction'].search_count([('attendance_id', '=', i.id)])
            if i.check_in and i.check_out:
                ci = i.check_in + timedelta(hours=7)
                co = i.check_out + timedelta(hours=7)
                if check_data == 0:
                    self.create({
                        'name': i.employee_id.id,
                        'tanggal': i.date_fd,
                        'worked_hours': i.worked_hours,
                        "check_in": str(ci)[11:],
                        "check_out": str(co)[11:],
                        'attendance_id': i.id
                    })

