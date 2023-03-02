from odoo import fields, models, api


class HrPerijinan(models.Model):
    _name = 'hr.perijinan'

    description = fields.Char(string="Description", required="1")
    from_date = fields.Date(string="From Date (MM/DD/YYY)", required="1")
    to_date = fields.Date(string="To Date (MM/DD/YYY)", required="1")
    status = fields.Selection([("active", "ACTIVE"), ('inactive', 'INACTIVE')], string="Status", required="1")
    note = fields.Char(string="Note")
    tipe = fields.Many2one('tipe.perijinan', string="Tipe")

class TipePerijinan(models.Model):
    _name = 'tipe.perijinan'

    name = fields.Char(string="Nama")