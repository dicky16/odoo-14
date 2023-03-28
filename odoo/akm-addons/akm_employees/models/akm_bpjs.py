from odoo import fields, models


class AkmBpjs(models.Model):
    _name = 'akm.bpjs'

    employee_id = fields.Many2one("hr.employee", "Employee", ondelete="cascade")
    type = fields.Selection([('kes', 'Kes'), ('tk', 'TK')], string='Type', default='tk')
    # program_tk = fields.Many2many('program.tk', string='Program TK')
    program_tk_ids = fields.Many2many('program.tk', 'bpjs_program_rel', 'bpjs_id', 'program_id', string='Program TK')
    program_tk = fields.Selection([('jkk', 'JKK'), ('jht', 'JHT'), ('jkm', 'JKM'), ('jp', 'JP')], string='Program TK')
    status_kes = fields.Selection([('ya', 'Terdaftar'), ('tidak', 'PBI'), ('belum', 'Belum Terdaftar')], string='Status Kes')
    no = fields.Char(string='No Kartu')
    iuran = fields.Integer(string='Iuran')
    image = fields.Image(string='Foto Kartu BPJS TK')

class ProgramTk(models.Model):
    _name = 'program.tk'

    name = fields.Char(string='Name', required=True )