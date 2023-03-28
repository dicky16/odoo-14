from odoo import fields, models, api

class HrTraining(models.Model):
    _name = 'hr.training'

    name = fields.Char(string="Nama Training")
    pay_location = fields.Many2one('pay.location', string="Pay Loc")
    pay_group = fields.Many2one("pay.group", string="Pay Group")
    pay_department = fields.Many2one('pay.department', string='Pay Dept')
    training_type = fields.Many2one('hr.training.type', string="Jenis")
    date = fields.Date(string="Date")
    pembicara = fields.Char(string="Pembicara")
    image1 = fields.Image("Dokumentasi")
    image2 = fields.Image("Dokumentasi")
    image3 = fields.Image("Dokumentasi")
    note1 = fields.Char("Note")
    note2 = fields.Char("Note")
    note3 = fields.Char("Note")
    note = fields.Char(string="Deskripsi")
    jumlah_peserta = fields.Integer(string="Jumlah Peserta")
    employee_id = fields.Many2many("hr.employee",string="Employee")
    document = fields.Binary(string="Document")
    daftar_hadir = fields.Binary(string="Daftar Hadir")
    location = fields.Char(string="Lokasi")
    start_time = fields.Float(string="Start Time")
    end_time = fields.Float(string="End Time")
    bagian = fields.Char(string="Bagian")
    
class HrTrainingType(models.Model):
    _name = 'hr.training.type'

    name = fields.Char(string="Training Type")
