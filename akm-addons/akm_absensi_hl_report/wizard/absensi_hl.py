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

class AbsensiHlWizard(models.TransientModel):
    _name = 'absensi.hl.wizard'

    date_from = fields.Date(string="Date From", required=True,default=fields.Date.context_today)
    date_to = fields.Date(string="Date To", required=True,default=fields.Date.context_today)
    status = fields.Selection([('tetap', 'Tetap'), ('kontrak', 'Kontrak'), ('hl', 'HL'), ('borongan', 'Borongan')],
                              string='Status')
    is_active = fields.Boolean('Active Employee', default=True)
    pay_location = fields.Many2one('pay.location', "Pay Location")
    pay_group = fields.Many2one('pay.group', string='Pay Group')
    pay_department = fields.Many2one('pay.department', string='Pay Dept')
    employee_id = fields.Many2one('hr.employee', string='Employee')

    report_file = fields.Binary('File', readonly=True)
    xls_report_name = fields.Text(string='File Name')
    is_printed = fields.Boolean('Printed', default=False)


    def export_details(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'absensi.hl.wizard'
        datas['form'] = self.read()[0]
        tz = pytz.timezone(self._context.get('tz', 'utc') or 'utc')

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Sheet 1')
        worksheet.set_landscape()
        fl = 'Absensi '+ fields.Date.today().strftime('%d-%m-%Y')+'.xlsx'

        bold = workbook.add_format({'bold': True, 'align': 'center'})
        text = workbook.add_format({'font_size': 12, 'align': 'center'})

        dom = []
        if self.status:
            dom.append(('pay_status', '=', self.status))
        if self.pay_location:
            dom.append(('pay_location', '=', self.pay_location.id))
        if self.pay_group:
            dom.append(('pay_group', '=', self.pay_group.id))
        if self.pay_department:
            dom.append(('pay_department', '=', self.pay_department.id))
        if self.employee_id:
            dom.append(('employee_id', '=', self.employee_id.id))
        if self.is_active:
            dom.append(('empl_active', '=', self.is_active))

        date_to = self.date_to + timedelta(days=1)
        datas = self.env['hr.work.entry'].read_group(
            [('date_start','>=',self.date_from),('date_start','<',date_to)]+dom,
            ['employee_id'], ['employee_id'], lazy=False
        )
        # else:
        #     # rec = self.env[context.get('active_model')].search([('id', 'in', datas['ids'])])
        #     datas = self.env['hr.work.entry'].read_group(
        #         [], ['employee_id'], ['employee_id'],lazy=False)
        total_days = self.date_to - self.date_from
        print('rec', datas)
        worksheet.set_column(0, 1, 15)
        worksheet.set_column(2, 2, 30)
        worksheet.set_column(3, 8, 15)
        worksheet.write(0, 0, 'No', bold)
        worksheet.write(0, 1, 'NIK', bold)
        worksheet.write(0, 2, 'NIK Pendek', bold)
        worksheet.write(0, 3, 'Nama Karyawan', bold)
        worksheet.write(0, 4, 'Pay Location', bold)
        worksheet.write(0, 5, 'Pay Group', bold)
        worksheet.write(0, 6, 'Pay Dept', bold)
        worksheet.write(0, 7, 'Bank Account', bold)
        worksheet.write(0, 8, 'Bank Name', bold)
        worksheet.write(0, 9, 'GaPok', bold)
        title_date = self.date_from
        for i in range(total_days.days+1):
            date = title_date + timedelta(days=i)
            worksheet.write(0, 10 + i, str(date.strftime("%d")), bold)
        worksheet.write(0, total_days.days+1+10, 'Tot WH', bold)
        worksheet.write(0, total_days.days+2+10, 'Tot Alpha', bold)
        worksheet.write(0, total_days.days+3+10, 'Tot Ijin', bold)
        worksheet.write(0, total_days.days+4+10, 'Tot Surat Dokter', bold)
        worksheet.write(0, total_days.days+5+10, 'Tot Cuti', bold)
        worksheet.write(0, total_days.days+6+10, 'Tot Ijin Pabrik', bold)
        worksheet.write(0, total_days.days+7+10, 'Tot', bold)
        row = 1
        col = 0
        row_num = 1
        dura = []
        print('employee')
        for da in datas:
            emp = self.env['hr.employee'].browse([da['employee_id'][0]])

            if not emp:
                continue
            # elif emp.pay_location.id != self.pay_location_id.id:
            #     continue
            if emp.contract_id.wage_type=='monthly':
                gapok = emp.contract_id.wage or 0
            else:
                gapok = emp.contract_id.hourly_wage or 0

            # worksheet.set_row(row_num, 98)
            worksheet.write(row, col, row_num, text)
            row_num = row_num + 1
            worksheet.write(row, col + 1, emp.pin or '', text)
            worksheet.write(row, col + 2, emp.barcode or '', text)
            worksheet.write(row, col + 3, emp.name, text)
            worksheet.write(row, col + 4, emp.pay_location.name or '', text)
            worksheet.write(row, col + 5, emp.pay_group.name or '', text)
            worksheet.write(row, col + 6, emp.pay_department.name or '', text)
            worksheet.write(row, col + 7, emp.bank_account_id.acc_number or '', text)
            worksheet.write(row, col + 8, emp.bank_account_id.acc_holder_name or '', text)
            worksheet.write(row, col + 9, gapok, text)

            date_from = datetime.combine(self.date_from, datetime.min.time())-timedelta(hours=7)
            date_to = datetime.combine(self.date_to+timedelta(days=1), datetime.min.time())-timedelta(hours=7)
            attendance = self.env['hr.work.entry'].search([
                ("employee_id", "=", da['employee_id'][0]),
                ('date_start', '>=', date_from),
                ('date_start', '<', date_to),
            ], order='date_start asc')
            column = 10
            row_date = self.date_from
            total_day = self.date_to - self.date_from
            tot_dura = 0
            tot_a= tot_i= tot_sd= tot_c= tot_ip= 0
            for i in range(total_day.days+1):
                date = row_date + timedelta(days=i)
                subtot = 0
                hangka = 0
                hhuruf = ''
                for j in attendance:
                    if date == j.date_start.astimezone(pytz.timezone('Asia/Jakarta')).date():
                        leave = j.work_entry_type_id.is_leave if j.work_entry_type_id else False
                        if not leave:
                            subtot += j.duration
                            hangka += j.duration
                            # worksheet.write(row, column, subtot, text)
                            tot_dura += j.duration
                            hhuruf = j.work_entry_type_id.code
                        else:
                            hhuruf = j.work_entry_type_id.code
                            # worksheet.write(row, column, j.work_entry_type_id.code, text)
                            if j.work_entry_type_id.code=='A': tot_a +=1
                            elif j.work_entry_type_id.code=='I': tot_i +=1
                            elif j.work_entry_type_id.code=='IP': tot_ip +=1
                            elif j.work_entry_type_id.code=='SD': tot_sd +=1
                            elif j.work_entry_type_id.code=='IM': tot_c +=1
                        # break

                worksheet.write(row, column, hhuruf, text)
                if emp.join2 > date:
                    worksheet.write(row, column, '-', text)
                elif emp.pay_location.name.lower() in ["staff", "bulanan"] and hhuruf == "M":
                    worksheet.write(row, column, "", text)
                elif hangka == 0 and hhuruf == "M":
                    worksheet.write(row, column, "0", text)
                elif hangka > 0 and hhuruf == "M":
                    worksheet.write(row, column, hangka, text)
                column += 1

            worksheet.write(row, column, tot_dura, text)
            if emp.pay_location.name.lower() in ["staff", "bulanan"]:
                worksheet.write(row, column, "", text)
            worksheet.write(row, column+1, tot_a, text)
            worksheet.write(row, column+2, tot_i, text)
            worksheet.write(row, column+3, tot_sd, text)
            worksheet.write(row, column+4, tot_c, text)
            worksheet.write(row, column+5, tot_ip, text)
            subtot= tot_a+tot_i+tot_sd+tot_c+tot_ip
            worksheet.write(row, column+6, subtot, text)

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
            'res_model': 'absensi.hl.wizard',
            'target': 'new',
            'context': ctx,
            'res_id': self.id,
        }

