from odoo import fields, models, api
from datetime import datetime

class HrPerijinan(models.Model):
    _name = 'hr.perijinan'

    description = fields.Char(string="Description", required="1")
    from_date = fields.Date(string="From Date", required="1")
    to_date = fields.Date(string="To Date")
    time = fields.Boolean(string="Unlimited Time", store=True)
    status = fields.Selection([("active", "ACTIVE"), ('inactive', 'INACTIVE')], string="Status", required="1")
    note = fields.Char(string="Note")
    tipe = fields.Many2one('tipe.perijinan', string="Tipe")
    document = fields.Binary("Document")
    is_expired = fields.Boolean(string="Expired", default=False)
    document_number = fields.Char(string="Document Number")
    penerbit = fields.Many2one('penerbit.perijinan', string="Penerbit")
    
    @api.onchange("time")
    def onchange_time(self):
        for x in self:
            if x.time:
                x.to_date = ""

    def check_expired(self):
        now = datetime.now().date()
        to_date = self.env["hr.perijinan"].search([
            ('status', '=', 'active'),
            ('time', "=", False)
        ])
        for x in to_date:
            date = x.to_date - now
            if date.days <= 30:
                x.is_expired = True
                print(date.days)

class TipePerijinan(models.Model):
    _name = 'tipe.perijinan'

    name = fields.Char(string="Nama")

class PenerbitPerijinan(models.Model):
    _name = 'penerbit.perijinan'

    name = fields.Char(string="Nama")
