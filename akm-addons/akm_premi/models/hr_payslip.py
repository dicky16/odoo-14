# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime
from collections import defaultdict
from odoo.tools import date_utils

class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    @api.model
    def _get_default_rule_ids(self):
        return []

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    pin = fields.Char(string="NIK", related='employee_id.pin', store=True)
    barcode = fields.Char(string="Old NIK", related='employee_id.barcode', store=True)
    pay_location = fields.Many2one('pay.location', string='Pay Loc', related='employee_id.pay_location', store=True)
    pay_group = fields.Many2one('pay.group', string='Pay Group', related='employee_id.pay_group', store=True)
    pay_department = fields.Many2one('pay.department', string='Pay Dept', related='employee_id.pay_department', store=True)
    premi_wage = fields.Monetary(compute='_compute_basic_net')
    bpjs_wage = fields.Monetary(compute='_compute_basic_net')
    spsi_wage = fields.Monetary(compute='_compute_basic_net')
    potongan_wage = fields.Monetary(compute='_compute_basic_net', string="Potongan Lain")
    insentif_wage = fields.Monetary(compute='_compute_basic_net', string="Insentif")
    gross_wage = fields.Monetary(compute='_compute_basic_net', string="Gross")
    additional_ids = fields.Many2many('hr.payslip.add', string='Iuran')
    monthly_wage = fields.Monetary(string="Monthly Wage", related='employee_id.contract_id.wage')
    hourly_wage = fields.Monetary(string="Hourly Wage", related='employee_id.contract_id.hourly_wage')
    sum_worked_hours = fields.Float(compute='_compute_worked_hours', string="Worked Hours", store=True, digits=(10,1))

    def _get_new_worked_days_lines(self):
        if self.struct_id.use_worked_day_lines:
            # computation of the salary worked days
            worked_days_line_values = self._get_worked_day_lines(check_out_of_contract=False)
            worked_days_lines = self.worked_days_line_ids.browse([])
            for r in worked_days_line_values:
                r['payslip_id'] = self.id
                worked_days_lines |= worked_days_lines.new(r)
            return worked_days_lines
        else:
            return [(5, False, False)]

    @api.depends('worked_days_line_ids.number_of_hours', 'worked_days_line_ids.is_paid')
    def _compute_worked_hours(self):
        for payslip in self:
            payslip.sum_worked_hours = sum([line.number_of_hours for line in payslip.worked_days_line_ids])

    def _compute_basic_net(self):
        for payslip in self:
            payslip.basic_wage = payslip._get_salary_line_total('BASIC') + payslip._get_salary_line_total('GAPOK')
            payslip.premi_wage = payslip._get_salary_line_total('PREMI') if payslip.additional_ids.filtered(lambda x: x.display_name == 'PREMI') else 0
            payslip.net_wage = payslip._get_salary_line_total('NET') if payslip.additional_ids.filtered(lambda x: x.display_name == 'NET') else 0
            payslip.bpjs_wage = payslip._get_salary_line_total('BPJS') if payslip.additional_ids.filtered(lambda x: x.display_name == 'BPJS') else 0
            payslip.spsi_wage = payslip._get_salary_line_total('SPSI') if payslip.additional_ids.filtered(lambda x: x.display_name == 'SPSI') else 0

            lines = payslip.input_line_ids.filtered(lambda line: line.amount<0)
            payslip.potongan_wage = abs(sum([line.amount for line in lines]))
            lines = payslip.input_line_ids.filtered(lambda line: line.amount>0)
            payslip.insentif_wage = sum([line.amount for line in lines])

            payslip.gross_wage = payslip.basic_wage+payslip.premi_wage+payslip.insentif_wage

    def _get_worked_day_lines_values(self, domain=None):
        self.ensure_one()
        res = []
        hours_per_day = self._get_worked_day_lines_hours_per_day()
        work_hours = self.contract_id.with_context(weekly=True)._get_work_hours(self.date_from, self.date_to, domain=domain)
        work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
        biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
        add_days_rounding = 0

        # work_entries = self.env['hr.work.entry'].read_group(
        #     self.contract_id._get_work_hours_domain(self.date_from, self.date_to, domain=domain, inside=True),
        #     ['hours:sum(duration)'],
        #     ['work_entry_type_id']
        # )
        for point1, point2 in work_hours_ordered:
            week = 0
            work_entry_type_id = False
            if point1:
                week = int(point1.split('-')[0])
                work_entry_type_id = int(point1.split('-')[1])
            if not work_entry_type_id:
                continue
            hours = float(point2.split('-')[0])
            counts = int(point2.split('-')[1])
            work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
            # if work_entry_type.is_leave:
            days = counts
            # else:
            #     days = round(hours / hours_per_day, 5) if hours_per_day else 0
            if work_entry_type_id == biggest_work:
                days += add_days_rounding
            day_rounded = self._round_days(work_entry_type, days)
            add_days_rounding += (days - day_rounded)
            attendance_line = {
                'sequence': work_entry_type.sequence,
                'week': week,
                'work_entry_type_id': work_entry_type_id,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        return res

class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'
    _order = 'week, sequence'

    week = fields.Integer(string='Week')
    code = fields.Char(string='Code', compute='_get_code', store=True)

    @api.depends('work_entry_type_id','week')
    def _get_code(self):
        for x in self:
            if x.week:
                x.code = str(x.week)+x.work_entry_type_id.code
            else:
                x.code = x.work_entry_type_id.code

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    additional_ids = fields.Many2many('hr.payslip.add', string='Potongan')

class HrPayslipAdditional(models.Model):
    _name = 'hr.payslip.add'

    name = fields.Char(string='Name')
