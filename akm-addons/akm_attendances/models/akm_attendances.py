from odoo import models, fields, api, exceptions, _
import requests
import json
from datetime import datetime, timedelta
import math
import pytz
from pytz import timezone, UTC, utc


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    _description = 'akm_attendances'

    id_check_in = fields.Integer(string='ID Check In')
    id_check_out = fields.Integer(string='ID Check Out')
    date_fd = fields.Date(string='Date in Face Detector')
    worked_hours = fields.Float(string='Worked Hours')
    barcode = fields.Char(string='Old NIK', readonly=True, related='employee_id.barcode', store=True)
    nik = fields.Char(string='NIK', readonly=True, related='employee_id.pin', store=True)
    pay_department = fields.Many2one('pay.department', string='Pay Department', related='employee_id.pay_department')
    pay_group = fields.Many2one('pay.group', string='Pay Group', related='employee_id.pay_group')

    def get_attendances(self):
        now = datetime.now() - timedelta(days=5)
        date = now.strftime("%Y-%m-%d")

        data_ci = []
        data_co = []
        data_ci.extend(self.env['fd.attendances'].search([
            ("date_fd", ">=", date),
            ("punch_state_display", "=", "Check In"),
            # ("terminal_sn", "!=", "CL9M205160564")
        ]))
        data_co.extend(self.env['fd.attendances'].search([
            ("date_fd", ">=", date),
            ("punch_state_display", "=", "Check Out"),
            # ("terminal_sn", "!=", "CL9M205160564")
        ]))

        for i in data_ci:
            check_in_attendance = self.env["hr.attendance"].search_count([
                ("employee_id", "=", i.name.id), ("date_fd", "=", i.date_fd)
            ])
            if check_in_attendance == 0:
                self.create({
                    "check_in": i.punch_time,
                    "employee_id": i.name.id,
                    "date_fd": i.date_fd,
                    "id_check_out": 0,
                })
            else:
                self.env["hr.attendance"].search([
                    ("employee_id", "=", i.name.id),
                    ("date_fd", "=", i.date_fd),
                    ("check_in", "<", i.punch_time)
                ]).write({
                    "check_in": i.punch_time,
                })

        for i in data_co:
            check_out_attendance = self.env["hr.attendance"].search_count([
                ("employee_id", "=", i.name.id), ("date_fd", "=", i.date_fd), ("check_out", "<", i.punch_time)
            ])
            print(i.punch_time.hour)
            # if check_out_attendance == 0:
            #     self.env['hr.attendance'].search([
            #         ("employee_id", "=", i.name.id),
            #         ("date_fd", "=", i.date_fd),
            #         ("id_check_out", "=", 0)
            #     ]).write({
            #         "check_out": i.punch_time,
            #         "id_check_out": 1
            #     })
            # else:
            #     self.env["hr.attendance"].search([
            #         ("employee_id", "=", i.name.id),
            #         ("date_fd", "=", i.date_fd),
            #         ("check_out", ">", i.punch_time)
            #     ]).write({
            #         "check_out": i.punch_time,
            #     })

    @api.model
    def get_attendances_yp(self, nik=None,dfrom=None):
        dom = []
        if nik:
            dom = [('nik','=',nik)]
        if dfrom:
            # converting time to users timezone
            fromtime = datetime.strptime(dfrom,'%Y-%m-%d')-timedelta(hours=7)
            dom.append(('punch_time','>',fromtime.strftime('%Y-%m-%d %H:%M:%S')))
        todel = self.env['fd.attendances'].search([('attendance_id','=',-1)]+dom)
        todel.write({'attendance_id': 0})
        real_att = self.env['fd.attendances'].search([("attend_id",'=',False),("attendance_id",'>=',0)]+dom, order='punch_time asc')
        count=0
        for rat in real_att:
            count +=1
            if rat.punch_time.hour>17:
                tanggal = rat.punch_time.replace(hour=17, minute=0, second=0)
            else:
                tanggal = rat.punch_time.replace(hour=0,minute=0,second=0) - timedelta(hours=7)
            tgl_from = tanggal.astimezone(pytz.timezone('utc'))
            tgl_to = tanggal + timedelta(days=1)
            tgl_to = tgl_to.astimezone(pytz.timezone('utc'))
            nik = rat.nik
            state = rat.punch_state_display
            if state=='Check In':
                cekatt = self.env['hr.attendance'].search([('nik','=',nik),
                                                           ('check_in','>',tgl_from),
                                                           ('check_in','<',tgl_to),('check_out','=',False)],
                                                          order='check_in desc', limit=1)
                if cekatt:
                    cekatt.check_in = rat.punch_time
                    rat.attend_id = cekatt.id
                else:
                    if not rat.name:
                        continue
                    attnew = self.create({
                        "check_in": rat.punch_time,
                        "check_out": False,
                        "employee_id": rat.name.id,
                        "date_fd": rat.punch_time.date(),
                    })
                    if attnew:
                        rat.attend_id = attnew.id
            if state=='Check Out':
                cekatt = self.env['hr.attendance'].search([('nik','=',nik),
                                                           ('check_out','=',False),
                                                           ('check_in','>',tgl_from-timedelta(days=1))],
                                                          order='check_in asc')
                for catt in cekatt:
                    cek_batas = rat.punch_time-catt.check_in
                    if cek_batas<timedelta(hours=18) and cek_batas>=timedelta(seconds=1):
                        catt.check_out = rat.punch_time.strftime('%Y-%m-%d %H:%M:%S')
                        rat.attend_id = catt.id
                        break
                    else:
                        # rat.attend_id = catt.id
                        continue
                if not cekatt or len(cekatt)==0:
                    rat.attendance_id = -1
                    continue

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                if attendance.check_out < attendance.check_in:
                    continue

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        for attendance in self:
            if not attendance.employee_id or not attendance.check_in:
                print('no employee or check in')
                continue
                
            last_attendance_before_check_in = self.env['hr.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                print('last_attendance_before_check_in')
            if not attendance.check_out:
                print('not attendance.check_out')
                no_check_out_attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
                if no_check_out_attendances:
                    print('no_check_out_attendances')
            else:
                last_attendance_before_check_out = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_in', '<', attendance.check_out),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
                if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                    print('last_attendance_before_check_out')
