# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class company(models.Model):
    _inherit = 'res.company'

    use_calendar = fields.Boolean(string='Use Calendar')
    calendar_id = fields.Many2one('resource.calendar', 'Default Calendar')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    use_calendar = fields.Boolean(string='Use Calendar', related='company_id.use_calendar', readonly=False)
    calendar_id = fields.Many2one('resource.calendar', 'Default Calendar', related='company_id.calendar_id', readonly=False)