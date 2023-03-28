from odoo import fields, models, api, _

class PayLocation(models.Model):
    _name = 'pay.location'

    name = fields.Char(string='Name', required=True)

class PayGroup(models.Model):
    _name = 'pay.group'

    name = fields.Char(string='Name', required=True)

class PayDepartment(models.Model):
    _name = 'pay.department'
    _order = 'name'

    name = fields.Char(string='Name', required=True)

class HrDivisi(models.Model):
    _name = 'hr.divisi'

    name = fields.Char(string='Name', required=True)

class DepartmentSub(models.Model):
    _name = 'department.sub'

    name = fields.Char(string='Name', required=True)

class HrSection(models.Model):
    _name = 'hr.section'

    name = fields.Char(string='Name', required=True)

class EmployeeGroup(models.Model):
    _name = 'employee.group'

    name = fields.Char(string='Name', required=True)

class HrPph21(models.Model):
    _name = 'hr.pph21'

    name = fields.Char(string='Name', required=True)

class GrupBorongan(models.Model):
    _name = 'hr.borongan'

    name = fields.Char(string='Name', required=True)
    user_ids = fields.Many2many('res.users', string='Users')

class HrKoperasi(models.Model):
    _name = 'hr.koperasi'

    name = fields.Char(string='Name', required=True)

class HrCabang(models.Model):
    _name = 'hr.cabang'

    name = fields.Char(string='Name', required=True)

class HrStatus(models.Model):
    _name = 'hr.status'

    name = fields.Char(string='Name', required=True)
