# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from math import ceil
from datetime import datetime

class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    def week_of_month(self,dt):
        dom = dt.day
        if dom <=7:
            res = 1
        elif dom >7 and dom<=15:
            res = 2
        elif dom >15 and dom<=22:
            res = 3
        else:
            res = 4
        return res

    week_number = fields.Integer(string='Week', compute='_get_week', store=True)

    @api.depends('date_start')
    def _get_week(self):
        for x in self:
            week = self.week_of_month(x.date_start)
            x.week_number=week