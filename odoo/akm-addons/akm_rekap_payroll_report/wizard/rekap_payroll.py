# -- coding: utf-8 --
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2019. All rights reserved.

from odoo import fields, models, api, _
import io
import base64
from odoo.tools.misc import xlsxwriter
from datetime import timedelta
import pytz
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class RekapPayrollWizard(models.TransientModel):
    _name = 'rekap.payroll.wizard'

    batch_id = fields.Many2one('hr.payslip.run', string='Batch')
    filter_state = fields.Selection([('all', 'All'), ('done', 'Done')], default='all', string='Filter Status')
    # payslip_ids = fields.Many2many('hr.payslip', string='Payslip')
    pay_location = fields.Many2one('pay.location', string="Pay Location")
    pay_group = fields.Many2one('pay.group', string='Pay Group')
    pay_department = fields.Many2one('pay.department', string='Pay Dept')

    report_file = fields.Binary('File', readonly=True)
    xls_report_name = fields.Text(string='File Name')
    is_printed = fields.Boolean('Printed', default=False)

    def export_details(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'rekap.payroll.wizard'
        datas['form'] = self.read()[0]
        tz = pytz.timezone(self._context.get('tz', 'utc') or 'utc')

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Sheet 1')
        worksheet.set_landscape()
        fl = 'Payroll '+ fields.Date.today().strftime('%d-%m-%Y')+'.xlsx'

        bold = workbook.add_format({'bold': True, 'align': 'center'})
        text = workbook.add_format({'font_size': 12, 'align': 'center'})
        date_style = workbook.add_format({'text_wrap': True, 'num_format': 'dd-mm-yyyy'})

        dom = []
        if self.batch_id:
            dom.append(('payslip_run_id', '=', self.batch_id.id))
        if self.pay_location:
            dom.append(('pay_location', '=', self.pay_location.id))
        if self.pay_group:
            dom.append(('pay_group', '=', self.pay_group.id))
        if self.pay_department:
            dom.append(('pay_department', '=', self.pay_department.id))

        # kombi = self.env['hr.payslip.input.type'].read_group([('payslip_run_id','=',self.batch_id.id)],['input_type_id','is_positive'], ['input_type_id'], lazy=False)
        kombi = self.env['hr.payslip.input.type'].search([])
        records = self.env['hr.payslip'].search(dom, order='pin asc')

        print('kombinasi', kombi)
        potong = []
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 12,
        })
        worksheet.set_column(0, 1, 15)
        worksheet.set_column(2, 2, 30)
        worksheet.set_column(3, 8, 15)
        worksheet.merge_range('A1:U1', self.batch_id.name, merge_format)
        # worksheet.write(0, 0, self.batch_id.name, bold)
        worksheet.write(1, 0, 'No', bold)
        worksheet.write(1, 1, 'NIK', bold)
        worksheet.write(1, 2, 'Old NIK', bold)
        worksheet.write(1, 3, 'Nama Karyawan', bold)
        # worksheet.write(0, 4, 'Pph21 Status', bold)
        worksheet.write(1, 4, 'Pay Loc', bold)
        worksheet.write(1, 5, 'Pay Group', bold)
        worksheet.write(1, 6, 'Pay Dept', bold)
        worksheet.write(1, 7, 'WH', bold)
        worksheet.write(1, 8, 'Rp/Jam', bold)
        worksheet.write(1, 9, 'GaPok', bold) # ini
        mulai=9
        cint=mulai
        for pot in kombi:
            if pot.is_positive:
                cint +=1
                worksheet.write(1, cint, str(pot.name), bold)  # ini
                potong.append({'name':str(pot.name), 'id':cint,})
        # worksheet.write(0, 10, 'Premi', bold) # ini
        worksheet.write(1, cint+1, 'Gross', bold)
        worksheet.write(1, cint+2, 'BPJS', bold) # ini
        worksheet.write(1, cint+3, 'SPSI', bold) # ini
        mulai=cint+3
        cint=mulai
        for pot in kombi:
            if not pot.is_positive:
                cint +=1
                worksheet.write(1, cint, str(pot.name), bold)  # ini
                potong.append({'name':str(pot.name), 'id':cint,})
        worksheet.write(1, cint+1, 'THP', bold)
        worksheet.write(1, cint+2, 'Bank', bold)
        worksheet.write(1, cint+3, 'Bank Account', bold)
        worksheet.write(1, cint+4, 'Status Payroll', bold)
        row = 2
        col = 0
        row_num = 1
        print('employee')
        for pay in records:
            emp = self.env['hr.employee'].browse([pay.employee_id.id])
            if not emp:
                continue
            basic = pay.basic_wage
            premi = pay.premi_wage
            bpjs = pay.bpjs_wage*-1 or 0
            spsi = pay.spsi_wage*-1 or 0
            potongan = 0
            insentif = 0
            # worksheet.set_row(row_num, 98)
            worksheet.write(row, col, row_num, text)
            row_num = row_num + 1
            for p in potong:
                worksheet.write(row, p['id'], (0), text)

            worksheet.write(row, col + 1, emp.pin or '', text)
            worksheet.write(row, col + 2, emp.barcode or '', text)
            worksheet.write(row, col + 3, emp.name, text)
            # worksheet.write(row, col + 4, emp.pph21.name or '', text)
            worksheet.write(row, col + 4, emp.pay_location.name or '', text)
            worksheet.write(row, col + 5, emp.pay_group.name or '', text)
            worksheet.write(row, col + 6, emp.pay_department.name or '', text)
            worksheet.write(row, col + 7, pay.sum_worked_hours, text)
            worksheet.write(row, col + 8, pay.hourly_wage, text)
            worksheet.write(row, col + 9, (basic), text)
            # worksheet.write(row, col + 10, (premi), text)
            cint = 9
            for p in kombi:
                ketemu=False
                if p.is_positive:
                    cint += 1
                    for inp in pay.input_line_ids:
                        if p.name==inp.name:
                            ketemu = True
                            insentif += inp.amount
                            worksheet.write(row, cint, (inp.amount), text)
                    if not ketemu:
                        worksheet.write(row, cint, (0), text)

            worksheet.write(row, cint + 1, (basic+premi+insentif), text)
            worksheet.write(row, cint + 2, (bpjs), text)
            worksheet.write(row, cint + 3, (spsi), text)

            cint += 3
            for p in kombi:
                ketemu=False
                if not p.is_positive:
                    cint += 1
                    for inp in pay.input_line_ids:
                        if p.name==inp.name:
                            ketemu = True
                            potongan += inp.amount
                            worksheet.write(row, cint, (inp.amount), text)
                    if not ketemu:
                        worksheet.write(row, cint, (0), text)
            worksheet.write(row, cint+1, (basic+premi+bpjs+spsi+potongan+insentif), text)
            worksheet.write(row, cint+2, emp.account_bank.name or '', text)
            worksheet.write(row, cint+3, emp.bank_account_id.acc_number or '', text)
            worksheet.write(row, cint+4, pay.state, text)
            row = row + 1

        workbook.close()
        xlsx_data = output.getvalue()
        result = base64.encodebytes(xlsx_data)
        context = self.env.args
        ctx = dict(context[2])
        ctx.update({'report_file': result})
        ctx.update({'file': fl})

        self.xls_report_name = fl
        self.report_file = ctx['report_file']
        self.is_printed = True
        print('finalllyyy')
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rekap.payroll.wizard',
            'target': 'new',
            'context': ctx,
            'res_id': self.id,
        }

