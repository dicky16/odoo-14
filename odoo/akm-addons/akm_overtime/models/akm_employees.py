from odoo import fields, models, api, _, exceptions
import requests
import json
from datetime import datetime, timedelta
import datetime
import math

class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        if args is None:
            args = []
        domain = args + ['|', ('barcode', operator, name), ('name', operator, name)]
        return self._search(domain, limit=limit, access_rights_uid=name_get_uid)

    def name_get(self):
        res = []
        for x in self:
            name = x.name
            if self._context.get('params'):
                if self._context.get('params').get('model')=='overtime.request':
                    if x.barcode:
                        name = "(%s) %s" % (x.barcode, name)
            if self._context.get('model')=='overtime.request':
                if x.barcode:
                    name = "(%s) %s" % (x.barcode, name)
            res += [(x.id, name)]
        return res
