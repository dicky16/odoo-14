from odoo import fields, models, api, _, exceptions
import requests
import json
from datetime import datetime, timedelta
import datetime
import math

class Department(models.Model):
    _inherit = "hr.department"

    grade = fields.Selection([
        ('director', 'Director'),
        ('division', 'Division'),
        ('department', 'Department'),
        ('sub_department', 'Sub Department'),
        ('section', 'Section'),
        ('non', 'Non Managerial')], string='Grade')

class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    employee_code = fields.Integer(string='Employee Code')
    employee_id = fields.Integer(string='Employee ID')
    barcode = fields.Char(string='Old NIK')

    pay_location = fields.Many2one('pay.location', string='Pay Location')
    pay_group = fields.Many2one('pay.group', string='Pay Group')
    pay_department = fields.Many2one('pay.department', string='Pay Department')

    grade = fields.Selection([
        ('director', 'Director'),
        ('division', 'Division'),
        ('department', 'Department'),
        ('sub_department', 'Sub Department'),
        ('section', 'Section'),
        ('non', 'Non Managerial')], string='Grade')
    divisi = fields.Many2one('hr.department', string='Divisi', domain="[('grade', '=', 'division')]")
    department_id = fields.Many2one('hr.department', 'Department', domain="[('grade', '=', 'department')]")
    sub_department = fields.Many2one('hr.department', string='Sub Department',
                                     domain="[('grade', '=', 'sub_department')]")
    section = fields.Many2one('hr.department', string='Section',
                                     domain="[('grade', '=', 'section')]")

    pph21 = fields.Many2one('hr.pph21', string='PPH21 Status')
    join1 = fields.Date(string='Tanggal Masuk Pertama')
    join2 = fields.Date(string='Tanggal Join')
    hr_religion = fields.Selection(
        [('islam', 'Islam'), ('protestan', 'Kristen'), ('katolik', 'Katolik'), ('hindu', 'Hindu'),
         ('buddha', 'Buddha'), ('konghucu', 'Konghucu')], string='Agama')
    npwp = fields.Char(string='NPWP')
    mobile = fields.Char(string='Telpon 2', related='address_home_id.mobile', related_sudo=False, )
    age1 = fields.Char(string='Umur Masuk',compute="_get_age1")
    periode1 = fields.Char(string='Masa Kerja Pertama',compute="get_periode1", store=True)
    periode2 = fields.Char(string='Masa Kerja Join', compute="get_periode2", store=True)
    age2 = fields.Char(string='Umur', compute="_get_age2")
    #
    hr_bonus = fields.Boolean(string='Bonus')
    hr_costing = fields.Selection([('produksi', 'Produksi'), ('supporting', 'Supporting')])
    iuran_spsi = fields.Integer(string='Iuran SPSI')
    status = fields.Selection([('tetap', 'Tetap'), ('kontrak', 'Kontrak'), ('hl', 'HL'), ('borongan', 'Borongan')],
                              string='Status')
    status_karyawan = fields.Many2one('hr.status', string='Status Karyawan')
    departure_reason = fields.Selection([
        ('mutasi', 'Mutasi'), ('out', 'Out'), ('fired', 'Fired'),
        ('resigned', 'Resigned'),
        ('retired', 'Retired')
    ], string="Departure Reason", groups="hr.group_hr_user", copy=False, tracking=True)
    hr_group = fields.Selection([('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D'), ('e', 'E'), ('f', 'F'), ('g', 'G'), ],
                                string='Group')
    hr_group_id = fields.Many2one('employee.group', string='Group')
    core_proses = fields.Selection([('core', 'Core'), ('proses', 'Proses')], string='Core/Proses')

    vaccine1 = fields.Boolean(string='Vaccine 1')
    vaccine2 = fields.Boolean(string='Vaccine 2')
    booster1 = fields.Boolean(string='Booster 1')
    booster2 = fields.Boolean(string='Booster 2')
    #
    ptkp_category_id = fields.Char(string='PTKP')
    bpjs_ids = fields.One2many("akm.bpjs","employee_id", string="BPJS")

    no_bpjs_tk = fields.Char(string='No BPJS TK')
    program_ids = fields.Many2many('program.tk', 'employee_program_rel', 'employee_id', 'program_id', string='Program TK')
    iuran_tk = fields.Integer(string='Iuran TK')
    image_tk = fields.Image(string='Foto BPJS TK')

    no_bpjs_kes = fields.Char(string='No BPJS Kes')
    status_kes = fields.Selection([('ya', 'Terdaftar'), ('tidak', 'PBI'), ('belum', 'Belum Terdaftar')], string='Status Kes')
    iuran_kes = fields.Integer(string='Iuran Kes')
    image_kes = fields.Image(string='Foto BPJS Kes')

    ktp_address = fields.Text(string="Alamat KTP")
    ktp_kota = fields.Char(string="Kota KTP")
    uniform_size = fields.Selection(
        [('s', 'S'), ('m', 'M'), ('l', 'L'), ('xl', 'XL'), ('xxl', 'XXL'), ('others', 'Others')],
        string="Ukuran Seragam")
    other_size = fields.Char("Other Size")
    document_sign = fields.Boolean(string='Serah Terima Jabatan')
    document_date = fields.Date(string='Tanggal Penyerahan Dokumen')
    grup_borongan = fields.Many2one('hr.borongan', string='Grup Borongan')
    koperasi = fields.Many2one("hr.koperasi", string="Koperasi")
    # cabang = fields.Many2one("hr.cabang", string="Cabang")
    # contract = fields.Many2one("hr.contract", string="Contract")
    # flag = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], string="Flag", default='active')
    area = fields.Char(string="FD Area")
    wage = fields.Char(string='Wage')
    hourly_wage = fields.Char(string='Hourly Wage')
    
    account_bank = fields.Many2one('res.bank',string='Bank', related='bank_account_id.bank_id', readonly=False)
    account_holder = fields.Char(string='Holder Name', related='bank_account_id.acc_holder_name', readonly=False)
    
    def run_employee_date(self):
        employee = self.env['hr.employee'].search([])
        for emp in employee:
            emp.get_periode1()
            emp.get_periode2()

    def get_date_hr_module(self, date1, date2):
        if date1 and date2:
            daysLeft = date1 - date2
            years = ((daysLeft.total_seconds()) / (365.242 * 24 * 3600))
            yearsInt = int(years)
            months = (years - yearsInt) * 12
            monthsInt = int(months)
            return '{0:d} th, {1:d}  bl.'.format(yearsInt, monthsInt)
        else:
            return '0 th, 0 bl'

    @api.depends('birthday', 'join1')
    def _get_age1(self):
        for record in self:
            record.age1 = record.get_date_hr_module(record.join1, record.birthday)

    @api.depends('birthday')
    def _get_age2(self):
        currentDate = datetime.date.today()
        for record in self:
            record.age2 = record.get_date_hr_module(currentDate, record.birthday)

    @api.depends('join1')
    def get_periode1(self):
        currentDate = datetime.date.today()
        for record in self:
            record.periode1 = record.get_date_hr_module(currentDate, record.join1)

    @api.depends('join2')
    def get_periode2(self):
        currentDate = datetime.date.today()
        for record in self:
            record.periode2 = record.get_date_hr_module(currentDate, record.join2)

    @api.onchange('ks_program')
    def onchange_ks_program(self):
        for record in self:
            if record.ks_program == 'tidak':
                record.ks_program_status = 'PBI'
            else:
                record.ks_program_status = ''

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

    def get_employees(self):
        url = "personnel/api/employees/"
        data = self.get_data(url)
        total_page = math.ceil(data['count'] / 10)
        now = datetime.datetime.now()

        data_employees = []
        for i in range(total_page):
            page_url = url + "?page=" + str(i)
            data = self.get_data(page_url)
            data_employees.extend(data['data'])

        for i in data_employees:
            area = str()
            for j in i['area']:
                area += str(j['id']) + ","
            employee = self.env['hr.employee'].search_count([('pin', '=', str(i['emp_code']))])
            if employee == 0:
                first_name = i['first_name'] if i['first_name'] else ''
                last_name = i['last_name'] if i['last_name'] else ''
                self.create({
                    'name': first_name + ' ' + last_name,
                    "employee_code": str(i['emp_code']),
                    "employee_id": str(i['id']),
                    "area": area,
                    "pin": str(i['emp_code']),
                })
                self.env.cr.commit()



    def action_to_api(self, employee_id, data_payload, method):
        self.ensure_one()
        url = "http://192.168.24.25:80/personnel/api/employees/" + str(employee_id) + "/"
        sync = "http://192.168.24.25:80/personnel/api/employees/resync_to_device/"
        payload = data_payload
        token = self.get_jwt()
        headers = {
            'Authorization': 'JWT' + ' ' + token,
        }

        sync_payload = {
            'employees': [employee_id]
        }
        response = requests.request(method, url, headers=headers, data=payload)
        response_sync = requests.request("POST", sync, headers=headers, data=sync_payload)
    
    def akm_archive_employee(self):
        # HrEmployeePrivate.action_to_api(self.employee_id, {}, "DELETE")
        for record in self:
            record.active = False
    #
    def akm_unarchive_employee(self):
        for record in self:
            record.active = True

    def write(self, vals):
        res = super(HrEmployeePrivate, self).write(vals)
        if len(self) == 1:
            for record in self:
                id = record.employee_id
                area = []
                if vals.get('name'):
                    data = record.area.split(",")[:-1]
                    for j in data:
                        area.append(int(j))
                    name = vals['name']
                    payload = {
                        "first_name": name,
                        "area": area,
                    }
                    #self.action_to_api(id, payload, "PUT")
            return res
            
    # def write(self, vals):
    #     res = super(HrEmployeePrivate, self).write(vals)
    #     for record in self:
    #         id = record.employee_id
    #         area = []
    #         if vals.get('name'):
    #             data = record.area.split(",")[:-1]
    #             for j in data:
    #                 area.append(int(j))
    #             name = vals['name']
    #             payload = {
    #                 "first_name": name,
    #                 "area": area,
    #             }
    #             self.action_to_api(id, payload, "PUT")
    #     return res

class HrDepartureWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    document_sign = fields.Boolean(string='Serah Terima Jabatan')
    document_date = fields.Date(string='Tanggal Penyerahan Dokumen')
    departure_reason = fields.Selection(selection=[('mutasi', 'Mutasi'), ('out', 'Out'), ('fired', 'Fired'),
                                                   ('resigned', 'Resigned'),
                                                   ('retired', 'Retired')], string='Out Type', default='out')
    #
    def action_register_departure(self):
        res = super(HrDepartureWizard, self).action_register_departure()
        # HrEmployeePrivate.akm_archive_employee(HrEmployeePrivate)
        employee = self.employee_id
        employee.active = False
        employee.document_sign = self.document_sign
        employee.document_date = self.document_date
        return res
        

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    partner_id = fields.Many2one('res.partner', 'Account Holder', required=False, ondelete='cascade', index=True, domain=['|', ('is_company', '=', True), ('parent_id', '=', False)])
