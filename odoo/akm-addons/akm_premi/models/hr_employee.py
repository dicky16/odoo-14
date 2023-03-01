# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime
from collections import defaultdict
from odoo.tools import date_utils
from odoo.osv import expression

class Employee(models.Model):
    _inherit = "hr.employee"

    nominal_premi = fields.Float('Premi', related='company_id.nominal_premi', store=True)
    iuran_spsi = fields.Integer(string='Iuran')
    iuran_anggota = fields.Integer(string='Iuran SPSI')
    end_contract_date = fields.Date(related='contract_id.date_end',groups="hr.group_hr_user")

class HrContract(models.Model):
    _inherit = 'hr.contract'

    def _get_work_hours_domain(self, date_from, date_to, domain=None, inside=True):
        if domain is None:
            domain = []
        domain = expression.AND([domain, [
            ('state', 'in', ['validated', 'draft','conflict']),
            ('contract_id', 'in', self.ids),
        ]])
        if inside:
            domain = expression.AND([domain, [
                ('date_start', '>=', date_from),
                ('date_stop', '<=', date_to)]])
        else:
            domain = expression.AND([domain, [
                '|', '|',
                '&', '&',
                    ('date_start', '>=', date_from),
                    ('date_start', '<', date_to),
                    ('date_stop', '>', date_to),
                '&', '&',
                    ('date_start', '<', date_from),
                    ('date_stop', '<=', date_to),
                    ('date_stop', '>', date_from),
                '&',
                    ('date_start', '<', date_from),
                    ('date_stop', '>', date_to)]])
        return domain

    def _get_work_hours(self, date_from, date_to, domain=None):
        """
        Returns the amount (expressed in hours) of work
        for a contract between two dates.
        If called on multiple contracts, sum work amounts of each contract.
        :param date_from: The start date
        :param date_to: The end date
        :returns: a dictionary {work_entry_id: hours_1, work_entry_2: hours_2}
        """

        generated_date_max = min(fields.Date.to_date(date_to), date_utils.end_of(fields.Date.today(), 'month'))
        self._generate_work_entries(date_from, generated_date_max)
        date_from = datetime.combine(date_from, datetime.min.time())
        date_to = datetime.combine(date_to, datetime.max.time())
        work_data = defaultdict(int)

        # First, found work entry that didn't exceed interval.
        if self.env.context.get('weekly', None):
            work_entries = self.env['hr.work.entry'].read_group(
                self._get_work_hours_domain(date_from, date_to, domain=domain, inside=True),
                ['hours:sum(duration)','week_number'],
                ['work_entry_type_id','week_number'], lazy=False
            )
        else:
            work_entries = self.env['hr.work.entry'].read_group(
                self._get_work_hours_domain(date_from, date_to, domain=domain, inside=True),
                ['hours:sum(duration)'],
                ['work_entry_type_id']
            )

        # work_data.update({data['work_entry_type_id'][0] if data['work_entry_type_id'] else False: data['hours'] for data in work_entries})
        work_data.update({str(data['week_number'])+"-"+str(data['work_entry_type_id'][0]) if data['work_entry_type_id'] else False: str(data['hours'])+'-'+str(data['__count']) for data in work_entries})

        # Second, find work entry that exceeds interval and compute right duration.
        # work_entries = self.env['hr.work.entry'].search(self._get_work_hours_domain(date_from, date_to, domain=domain, inside=False))
        #
        # for work_entry in work_entries:
        #     date_start = max(date_from, work_entry.date_start)
        #     date_stop = min(date_to, work_entry.date_stop)
        #     if work_entry.work_entry_type_id.is_leave:
        #         contract = work_entry.contract_id
        #         calendar = contract.resource_calendar_id
        #         employee = contract.employee_id
        #         contract_data = employee._get_work_days_data_batch(
        #             date_start, date_stop, compute_leaves=False, calendar=calendar
        #         )[employee.id]
        #
        #         work_data[work_entry.work_entry_type_id.id] += contract_data.get('hours', 0)
        #     else:
        #         dt = date_stop - date_start
        #         work_data[work_entry.work_entry_type_id.id] += dt.days * 24 + dt.seconds / 3600  # Number of hours
        return work_data

class HrDepartureWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    def action_register_departure(self):
        """If set_date_end is checked, set the departure date as the end date to current running contract,
        and cancel all draft contracts"""
        current_contract = self.employee_id.contract_id
        date_end = self.employee_id.contract_id.date_end

        super(HrDepartureWizard, self).action_register_departure()
        if self.set_date_end:
            self.employee_id.contract_ids.filtered(lambda c: c.state == 'draft').write({'state': 'cancel'})
            if current_contract:
                self.employee_id.contract_id.write({'date_end': date_end})
                self.employee_id.contract_id.write({'date_generated_to': self.departure_date})
