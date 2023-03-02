from odoo import fields, models, api

class HrFlagSts(models.Model):
    _name = 'hr.flag.sts'

    name = fields.Char(string='Name', required=True)