from odoo import models, fields, api, exceptions, _
import requests
import json
from datetime import datetime, timedelta
import math
from pytz import timezone, UTC, utc


class FdAttendances(models.Model):
    _name = 'fd.attendances'

    attendance_id = fields.Integer(string="Id")
    attend_id = fields.Many2one("hr.attendance", string="Attendance")
    emp_code = fields.Char()
    name = fields.Char(string="Name")
    punch_time = fields.Datetime()
    punch_state = fields.Integer()
    punch_state_display = fields.Char()
    work_code = fields.Char()
    area_alias = fields.Char()
    terminal_sn = fields.Char()
    terminal_alias = fields.Char()
    upload_time = fields.Datetime()
    name = fields.Many2one("hr.employee", string="Nama")
    nik = fields.Char(string="NIK", related='name.pin', store=True)
    barcode = fields.Char(string="Old NIK", related='name.barcode', store=True)
    pay_group = fields.Many2one('pay.group', string='Group', related='name.pay_group', store=True)
    pay_department = fields.Many2one('pay.department', string='Pay Department', related='name.pay_department',store=True)
    pay_location = fields.Many2one('pay.location', string='Pay Location', related='name.pay_location',store=True)

    def get_jwt(self):
        url = "http://192.168.24.25:80/jwt-api-token-auth/"

        payload = json.dumps({
            "username": "admin",
            "password": "AKM2022;"
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        return data['token']

    def get_data(self, url):
        base_url = "http://192.168.24.25:80/" + url
        payload = {}
        token = self.get_jwt()
        headers = {
            'Authorization': 'JWT' + ' ' + token,
        }
        response = requests.request("GET", base_url, headers=headers, data=payload)
        return response.json()

    def get_fd_attendance(self):
        #self.env['hr.employee'].get_employees()
        now = datetime.now() - timedelta(days=1)
        url = "iclock/api/transactions/"
        # count_total = url + "?start_time=2022-10-10&?end_time=2022-10-10"
        count_total = url + "?start_time=" + now.strftime("%Y-%m-%d") + " " + now.strftime("%H:%M:%S")
        data = self.get_data(count_total)
        total_page = math.ceil(data['count'] / 10) + 1
        data_attendances = []
        tz = self.env.user.tz

        for i in range(total_page):
            page_url = url + "?page=" + str(i) + "&start_time=" + now.strftime("%Y-%m-%d") + " " + now.strftime(
                "%H:%M:%S")
            # page_url = url + "?page=" + str(i) + "&start_time=2022-10-10&?end_time=2022-10-10"
            data = self.get_data(page_url)
            data_attendances.extend(data['data'])

        for i in data_attendances:
            # check_attendance = self.env['fd.attendances'].search_count([('attendance_id', '=', str(i['id']))])
            # if check_attendance == 0:
            datetime_api = datetime.strptime(i['punch_time'], '%Y-%m-%d %H:%M:%S')
            employees = self.env['hr.employee'].search([('pin', '=', str(i['emp_code']))])
            if len(employees) == 1:
                employee_id = employees.id
                apply_date_tz = str(timezone(tz or 'UTC').localize(datetime_api).astimezone(utc))[:19]
                attendance_id = i['id'] if employee_id else -1
                self.env['fd.attendances'].create({
                    'attendance_id': attendance_id,
                    'emp_code': i['emp_code'],
                    "name": employee_id,
                    'punch_time': apply_date_tz,
                    'punch_state': i['punch_state'],
                    'punch_state_display': i['punch_state_display'],
                    'work_code': i['work_code'],
                    'area_alias': i['area_alias'],
                    'terminal_sn': i['terminal_sn'],
                    'terminal_alias': i['terminal_alias'],
                    'upload_time': i['upload_time'],
                })
            # else:
            #     continue
        self.env['hr.attendance'].get_attendances_yp(dfrom='2022-10-01')
        self.env['hr.attendance'].calc_all_wh(cek_err=11)


    def get_fd_attendance_one_employee(self, date_start=None, date_stop=None, nik=None):
        try:
            self.env['hr.employee'].get_employees()
            now = datetime.now() - timedelta(days=1)
            url = "iclock/api/transactions/"
            count_total = url + "?start_time=" + date_start + "&?end_time=" + date_stop
            data = self.get_data(count_total)
            total_page = math.ceil(data['count'] / 10) + 1
            data_attendances = []
            tz = self.env.user.tz

            for i in range(total_page):
                page_url = url + "?page=" + str(i) + "&start_time=" + date_start + "&?end_time=" + date_stop
                print ("Test: "+page_url)
                data = self.get_data(page_url)
                if nik:
                    emp_data = list(filter(lambda x: x['emp_code'] == str(nik), data['data']))
                    data_attendances.extend(emp_data)
                else:
                    data_attendances.extend(data['data'])
            cint=0
            for i in data_attendances:
                cint +=1
                # check_attendance = self.env['fd.attendances'].search_count([('attendance_id', '=', str(i['id']))])
                # if check_attendance == 0:
                datetime_api = datetime.strptime(i['punch_time'], '%Y-%m-%d %H:%M:%S')
                employees = self.env['hr.employee'].search([('employee_code', '=', str(i['emp_code']))])
                if len(employees) == 1:
                    employee_id = employees.id
                    apply_date_tz = str(timezone(tz or 'UTC').localize(datetime_api).astimezone(utc))[:19]
                    attendance_id = i['id'] if employee_id else -1
                    self.env['fd.attendances'].create({
                        'attendance_id': attendance_id,
                        'emp_code': i['emp_code'],
                        "name": employee_id,
                        'punch_time': apply_date_tz,
                        'punch_state': i['punch_state'],
                        'punch_state_display': i['punch_state_display'],
                        'work_code': i['work_code'],
                        'area_alias': i['area_alias'],
                        'terminal_sn': i['terminal_sn'],
                        'terminal_alias': i['terminal_alias'],
                        'upload_time': i['upload_time'],
                    })
                # else:
                #     continue
            self.env['hr.attendance'].get_attendances_yp()
        except Exception as e:
            print(e)


class ConfirmationReal(models.TransientModel):
    _name = 'confirmation.real'

    def confirm_yes(self):
        self.env['fd.attendances'].get_fd_attendance()

    def cancel_button(self):
        return {
            'type': 'ir.actions.act_window_close'
        }

