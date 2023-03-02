# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class company(models.Model):
    _inherit = 'res.company'

    nominal_premi = fields.Float(string='Nominal Premi',default=100000)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    nominal_premi = fields.Float(string='Nominal Premi', related='company_id.nominal_premi', readonly=False)