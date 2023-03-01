from odoo import models, fields, api, exceptions, _
import requests
import json
from datetime import datetime, timedelta
import math
from pytz import timezone, UTC, utc


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    _description = 'akm_attendances'

    id_check_in = fields.Integer(string='ID Check In')
    id_check_out = fields.Integer(string='ID Check Out')
    date_fd = fields.Date(string='Date in Face Detector')
    worked_hours = fields.Integer(string='Worked Hours')
    barcode = fields.Char(string='Old NIK', readonly=True)
    nik = fields.Char(string='NIK', readonly=True, related='employee_id.pin')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        barcode = self.employee_id.barcode
        self.barcode = barcode

    def count_worked_hours(self, emp_code, date_fd, check_out):
        days = self.env['hr.attendance'].search(
            [('employee_id', '=', emp_code), ('date_fd', '=', date_fd), ('id_check_out', '=', 0)]).check_in.strftime(
            '%A')
        check_in = self.env['hr.attendance'].search(
            [('employee_id', '=', emp_code), ('date_fd', '=', date_fd)]).check_in
        check_out = datetime.strptime(check_out, '%Y-%m-%d %H:%M:%S')
        c_out = check_out.replace(microsecond=0, second=0, minute=0)
        if check_in.minute == 0:
            c_in = check_in.replace(microsecond=0, second=0, minute=0)
        else:
            c_in = check_in.replace(microsecond=0, second=0, minute=0) + timedelta(hours=1)

        if check_in.hour < 9 and days == 'Jumat':
            hours = (c_out - c_in) - timedelta(hours=1, minutes=30)
        else:
            hours = (c_out - c_in) - timedelta(hours=1)
        return round(hours.total_seconds() / 3600.0)

    def get_jwt(self):
        url = "http://127.0.0.1:8081/jwt-api-token-auth/"

        payload = json.dumps({
            "username": "bayu",
            "password": "merdeka123"
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        return data['token']

    def get_data(self, url):
        base_url = "http://127.0.0.1:8081/" + url
        payload = {}
        token = self.get_jwt()
        headers = {
            'Authorization': 'JWT' + ' ' + token,
        }
        response = requests.request("GET", base_url, headers=headers, data=payload)
        return response.json()

    def get_attendances(self):
        now = datetime.now() - timedelta(days=100)
        url = "iclock/api/transactions/"
        data = self.get_data(url)
        total_page = math.ceil(data['count'] / 10)
        data_attendances = []
        check_in = []
        check_out = []
        tz = self.env.user.tz

        for i in range(total_page):
            page_url = url + "?page=" + str(i) + "&?start_time=" + now.strftime("%Y-%m-%d") + "%20" + now.strftime(
                "%H:%M:%S")
            data = self.get_data(page_url)
            data_attendances.extend(data['data'])

        for i in data_attendances:
            if i['punch_state_display'] == 'Masuk':
                check_in.append(i)
            else:
                check_out.append(i)

        for i in check_in:
            check_in_datetime = str(datetime.strptime(i['punch_time'], '%Y-%m-%d %H:%M:%S'))
            date_fd = check_in_datetime[:10]
            datetime_api = datetime.strptime(i['punch_time'], '%Y-%m-%d %H:%M:%S')
            employee_data = self.env['hr.employee'].search([('employee_code', '=', str(i['emp_code']))])
            emp_code = employee_data.id
            apply_date_tz = str(timezone(tz or 'UTC').localize(datetime_api).astimezone(utc))[:19]
            if not emp_code:
                continue
            check_in_attendance = self.env['hr.attendance'].search_count(
                [('employee_id', '=', emp_code), ('date_fd', '=', date_fd)])
            if check_in_attendance == 0:
                self.create({
                    'check_in': apply_date_tz,
                    'employee_id': emp_code,
                    'id_check_in': i['id'],
                    'id_check_out': 0,
                    'date_fd': date_fd,
                })
            else:
                check_in_db = self.env['hr.attendance'].search(
                    [('employee_id', '=', emp_code), ('date_fd', '=', date_fd)]).check_in
                old_check_in_date = datetime.strptime(str(check_in_db), '%Y-%m-%d %H:%M:%S')
                new_check_in_date = datetime.strptime(str(apply_date_tz), '%Y-%m-%d %H:%M:%S')
                if new_check_in_date < old_check_in_date:
                    self.env['hr.attendance'].search([('employee_id', '=', emp_code), ('date_fd', '=', date_fd)]).write(
                        {
                            'check_in': apply_date_tz,
                            'id_check_in': i['id'],
                        })

        for i in check_out:
            check_out_datetime = str(datetime.strptime(i['punch_time'], '%Y-%m-%d %H:%M:%S'))
            date_fd = check_out_datetime[:10]
            datetime_api = datetime.strptime(i['punch_time'], '%Y-%m-%d %H:%M:%S')
            emp_code = self.env['hr.employee'].search([('employee_code', '=', str(i['emp_code']))]).id
            apply_date_tz = str(timezone(tz or 'UTC').localize(datetime_api).astimezone(utc))[:19]
            if not emp_code:
                continue
            check_out_attendance = self.env['hr.attendance'].search_count(
                [('employee_id', '=', emp_code), ('id_check_out', '=', 0), ('date_fd', '=', date_fd)])
            if check_out_attendance == 1:
                hours = self.count_worked_hours(emp_code, date_fd, apply_date_tz)
                if hours > 4:
                    self.env['hr.attendance'].search(
                        [('employee_id', '=', emp_code), ('date_fd', '=', date_fd), ('id_check_out', '=', 0)]).write({
                        'check_out': apply_date_tz,
                        'id_check_out': i['id'],
                        'worked_hours': hours,
                    })
            else:
                check_out_db = self.env['hr.attendance'].search(
                    [('employee_id', '=', emp_code), ('date_fd', '=', date_fd)]).check_out
                if check_out_db == False:
                    continue
                old_check_out_date = datetime.strptime(str(check_out_db), '%Y-%m-%d %H:%M:%S')
                new_check_out_date = datetime.strptime(str(apply_date_tz), '%Y-%m-%d %H:%M:%S')
                if new_check_out_date < old_check_out_date:
                    self.env['hr.attendance'].search(
                        [('employee_id', '=', emp_code), ('date_fd', '=', date_fd),
                         ('id_check_out', '!=', 0)]).write(
                        {
                            'check_out': new_check_out_date,
                            'id_check_out': i['id'],
                        })

    # def delete_attendance(self, attendances_id):
    #     url = "http://127.0.0.1:8081/iclock/api/transactions/" + str(attendances_id) + "/"
    #     print(url)
    #     payload = {}
    #     token = self.get_jwt()
    #     headers = {
    #         'Authorization': 'JWT' + ' ' + token,
    #     }
    #     response = requests.request("DELETE", url, headers=headers, data=payload)
    #
    # def unlink(self):
    #     check_in = self.mapped('id_check_in')
    #     check_out = self.mapped('id_check_out')
    #     for i in check_in:
    #         print(i)
    #         self.delete_attendance(i)
    #     for i in check_out:
    #         print(i)
    #         self.delete_attendance(i)
    #     return super(AkmAttendances, self).unlink()

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                if attendance.check_out < attendance.check_in:
                    continue

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        for attendance in self:
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
