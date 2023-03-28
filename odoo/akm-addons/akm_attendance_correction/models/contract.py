from odoo import fields, models, api, _
import locale
from collections import defaultdict
from datetime import date, datetime
from datetime import timedelta
from odoo import api, fields, models
import pytz
import json

class HrContract(models.Model):
    _inherit = 'hr.contract'

    date_generated_from = fields.Datetime(string='Generated From', readonly=False, required=True,
        default=lambda self: datetime.now().replace(hour=0, minute=0, second=0), copy=False)

    def _get_contract_work_entries_values(self, date_start, date_stop):
        res = super(HrContract, self)._get_contract_work_entries_values(date_start, date_stop)

        leave_entry_type = self.env.ref('hr_work_entry_contract.work_entry_type_leave')
        default_work_entry_type = self._get_default_work_entry_type()
        tambah = []
        for x in res:
            if x.get('work_entry_type_id'):
                wet = self.env['hr.work.entry.type'].browse([x['work_entry_type_id']])
                x['name'] = wet.code
                # Check ada Attendance
                start1 = x['date_start'].replace(hour=0, minute=0) - timedelta(hours=7, minutes=7)
                stop1 = x['date_start'].replace(hour=23, minute=59) - timedelta(hours=7, minutes=7)

                actual = self.env['hr.attendance'].search([('employee_id', '=', x['employee_id']),
                                                           ('check_in', '>', start1),
                                                           ('check_in', '<', stop1)], order='check_in asc')
                # if len(actual)>0:
                #     x['actual_in'] = actual[0].check_in
                #     if actual[0].check_out:
                #         x['actual_out'] = actual[0].check_out
                #         x['name'] = default_work_entry_type.code
                #         x['work_entry_type_id'] = default_work_entry_type.id
                #     else:
                #         x['actual_out'] = False
                #         x['name'] = leave_entry_type.code
                #         x['work_entry_type_id'] = leave_entry_type.id
                # if not wet.is_leave:
                # Cek ketersediaan attendance
                if len(actual) > 0:
                    x['actual_in'] = actual[0].check_in
                    actual_in = actual[0].check_in
                    date = actual_in + timedelta(hours=7, minutes=7)
                    day = date.weekday()
                    if actual[0].check_out:
                        x['actual_out'] = actual[0].check_out
                        x['name'] = default_work_entry_type.code
                        x['work_entry_type_id'] = default_work_entry_type.id
                    elif day == 6 and not actual[0].check_in or day == 6 and not actual[0].check_out:
                        x['actual_out'] = actual[0].check_out
                        x['name'] = default_work_entry_type.code
                        x['work_entry_type_id'] = wet.id
                    else:
                        x['actual_out'] = False
                        x['name'] = leave_entry_type.code
                        x['work_entry_type_id'] = leave_entry_type.id

                    i = 0
                    point = x
                    for y in actual:
                        if i > 0 and y.check_in and y.check_out:
                            buff = point.copy()
                            point['date_stop'] = y.check_in
                            buff['date_start'] = y.check_in
                            buff['date_stop'] = y.check_out
                            buff['actual_in'] = y.check_in

                            if y.check_out:
                                buff['actual_out'] = y.check_out
                                buff['name'] = default_work_entry_type.code
                                buff['work_entry_type_id'] = default_work_entry_type.id
                            elif day == 6 and not y.check_in or day == 6 and not y.check_out:
                                buff['actual_out'] = y.check_out
                                buff['name'] = default_work_entry_type.code
                                buff['work_entry_type_id'] = wet.id
                            else:
                                buff['actual_out'] = False
                                buff['name'] = leave_entry_type.code
                                buff['work_entry_type_id'] = leave_entry_type.id

                            tambah.append(buff)
                            point = buff
                        i += 1
                else:
                    if x['work_entry_type_id']:
                        curr_work_entry = self.env['hr.work.entry.type'].browse([x['work_entry_type_id']])
                        if curr_work_entry.code in [leave_entry_type.code, default_work_entry_type.code]:
                            x['name'] = leave_entry_type.code
                            x['work_entry_type_id'] = leave_entry_type.id

        res = res + tambah
        result = []
        for x in res:
            if x['date_start'] > x['date_stop']:
                continue
            # cek eksis WE
            eksis = self.env['hr.work.entry'].search([('employee_id', '=', x['employee_id']), ('active', '=', True),
                                                      ('date_start', '=', x['date_start'])])
            if len(eksis) > 0:
                continue
            result.append(x)
        return result


    # def _get_contract_work_entries_values(self, date_start, date_stop):
    #     res = super(HrContract, self)._get_contract_work_entries_values(date_start, date_stop)
    # 
    #     leave_entry_type = self.env.ref('hr_work_entry_contract.work_entry_type_leave')
    #     default_work_entry_type = self._get_default_work_entry_type()
    #     tambah = []
    #     for x in res:
    #         if x.get('work_entry_type_id'):
    #             wet = self.env['hr.work.entry.type'].browse([x['work_entry_type_id']])
    #             x['name'] = wet.code
    #             # Check ada Attendance
    #             start1 = x['date_start'].replace(hour=0,minute=0) - timedelta(hours=7, minutes=7)
    #             stop1 = x['date_start'].replace(hour=23,minute=59) - timedelta(hours=7, minutes=7)
    # 
    #             actual = self.env['hr.attendance'].search([('employee_id','=',x['employee_id']),
    #                                                        ('check_in','>',start1),
    #                                                        ('check_in','<',stop1)], order='check_in asc')
    #             # if not wet.is_leave:
    #                 # Cek ketersediaan attendance
    #             # if len(actual)>0:
    #             #     x['actual_in'] = actual[0].check_in
    #             #     if actual[0].check_out:
    #             #         x['actual_out'] = actual[0].check_out
    #             #         x['name'] = default_work_entry_type.code
    #             #         x['work_entry_type_id'] = default_work_entry_type.id
    #             #     else:
    #             #         x['actual_out'] = False
    #             #         x['name'] = leave_entry_type.code
    #             #         x['work_entry_type_id'] = leave_entry_type.id
    #             if len(actual)>0:
    #                 x['actual_in'] = actual[0].check_in
    #                 day = actual[0].check_in.weekday()
    #                 if actual[0].check_out:
    #                     x['actual_out'] = actual[0].check_out
    #                     x['name'] = default_work_entry_type.code
    #                     x['work_entry_type_id'] = default_work_entry_type.id
    #                 elif day == 6 and not actual[0].check_in or day == 6 and not actual[0].check_out:
    #                     x['actual_out'] = actual[0].check_out
    #                     x['name'] = default_work_entry_type.code
    #                     x['work_entry_type_id'] = wet.id
    #                 else:
    #                     x['actual_out'] = False
    #                     x['name'] = leave_entry_type.code
    #                     x['work_entry_type_id'] = leave_entry_type.id
    # 
    #                 i = 0
    #                 point = x
    #                 for y in actual:
    #                     if i>0 and y.check_in and y.check_out:
    #                         buff = point.copy()
    #                         point['date_stop'] = y.check_in
    #                         buff['date_start'] = y.check_in
    #                         buff['date_stop'] = y.check_out
    #                         buff['actual_in'] = y.check_in
    # 
    #                         if y.check_out:
    #                             buff['actual_out'] = y.check_out
    #                             buff['name'] = default_work_entry_type.code
    #                             buff['work_entry_type_id'] = default_work_entry_type.id
    #                         else:
    #                             buff['actual_out'] = False
    #                             buff['name'] = leave_entry_type.code
    #                             buff['work_entry_type_id'] = leave_entry_type.id
    # 
    #                         tambah.append(buff)
    #                         point = buff
    #                     i +=1
    #             else:
    #                 if x['work_entry_type_id']:
    #                     curr_work_entry = self.env['hr.work.entry.type'].browse([x['work_entry_type_id']])
    #                     if curr_work_entry.code in [leave_entry_type.code,default_work_entry_type.code]:
    #                         x['name'] = leave_entry_type.code
    #                         x['work_entry_type_id'] = leave_entry_type.id
    # 
    #     res = res + tambah
    #     result = []
    #     for x in res:
    #         if x['date_start']>x['date_stop']:
    #             continue
    #         # cek eksis WE
    #         eksis = self.env['hr.work.entry'].search([('employee_id','=',x['employee_id']),('active','=',True),
    #                                                   ('date_start','=',x['date_start'])])
    #         if len(eksis)>0:
    #             continue
    #         result.append(x)
    #     return result

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            structure_types = self.env['hr.payroll.structure.type'].search([
                '|',
                ('country_id', '=', self.company_id.country_id.id),
                ('country_id', '=', False)],order='id desc')
            if structure_types:
                self.structure_type_id = structure_types[0]
            elif self.structure_type_id not in structure_types:
                self.structure_type_id = False
