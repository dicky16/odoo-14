# -*- coding: utf-8 -*-
import xlsxwriter
import datetime
from time import gmtime, strftime
from odoo import models, fields, api
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx

class HrDisciplinaryXlsx(ReportXlsx):
    
    def generate_xlsx_report(self, workbook, data, records):
        domain = []
        report_name = 'Disciplinary Report'
        if not records.all_employee:
            domain.append(('employee_id', '=', records.employee.id))
        if not records.all_stages:
            domain.append(('disciplinary_stage', '=', records.disciplinary_stages.id))
        if records.from_date:
            domain.append(('date_diciplined', '>=', records.from_date))
        if records.to_date:
            domain.append(('date_diciplined', '<=', records.to_date))

        worksheet = workbook.add_worksheet(report_name[:31])
        company = records.env.user.company_id
        datetime.datetime.now()
        c_time = strftime("%Y-%m-%d", gmtime())
        worksheet.set_column('A:I', 20)
        bold = workbook.add_format({'bold': True,'font_name': 'Arial', 'font_size': 10,})
        merge_format = workbook.add_format({'bold': True,
            'border': 2, 'bottom': 2,'top': 2,'left': 2,'right': 2,
            'font_size': 15, 'font_name': 'Arial'})
        worksheet.merge_range('D1:G1', company.name, merge_format)
        worksheet.write(2,0, 'Title', bold)
        worksheet.write(2,1, 'Disciplinary Report', bold)
        worksheet.write(3,0, 'Company Name', bold)
        worksheet.write(3,1, company.name, bold)
        worksheet.write(4,0, 'Date', bold)
        worksheet.write(4,1, c_time, bold)
        worksheet.write(7,0, 'Annual Leave', bold)
        header = workbook.add_format({'bold': True,
            'border': 2, 'bottom': 2,
            'top': 2,'left': 2,'right': 2,
            'font_name': 'Arial', 'font_size': 10,})
        worksheet.write(9,0, 'Department', header)
        worksheet.write(9,1, 'Employee ID', header)
        worksheet.write(9,2, 'Employee Name', header)
        worksheet.write(9,3, 'Disciplined Date', header)
        worksheet.write(9,4, 'Disciplinary Stages', header)
        worksheet.write(9,5, 'Valid Until', header)
        worksheet.write(9,6, 'Reason of Disciplinary', header)
        i = 10
        normal_rows = workbook.add_format({'bold': False,
            'border': 2, 'bottom': 2,'top': 2,'left': 2,'right': 2,
            'font_name' : 'Arial', 
            'font_size': 10, })
        disciplinaries = self.env['disciplinary.history'].search(domain)
        for disciplinary in disciplinaries:
            worksheet.write(i, 0, disciplinary.employee_id.department_id.name, normal_rows)
            worksheet.write(i, 1, disciplinary.employee_id.id, normal_rows)
            worksheet.write(i, 2, disciplinary.employee_id.name, normal_rows)
            worksheet.write(i, 3, disciplinary.date_diciplined, normal_rows)
            worksheet.write(i, 4, disciplinary.disciplinary_stage.disciplinary_name, normal_rows)
            worksheet.write(i, 5, disciplinary.valid_until, normal_rows)
            worksheet.write(i, 6, disciplinary.reason_disciplinary, normal_rows)
            i = i + 1
        return workbook

HrDisciplinaryXlsx('report.disciplinary_report.xlsx',
            'disciplinary.report.wizard')

class DisciplinaryReportWizard(models.TransientModel):
    _name = 'disciplinary.report.wizard'

    all_employee = fields.Boolean()
    all_stages = fields.Boolean()
    from_date = fields.Date(required=True)
    to_date = fields.Date(required=True)
    employee = fields.Many2one('hr.employee', string="Employee",)
    disciplinary_stages = fields.Many2one('disciplinary.stage', string="Disciplinary Stages",)

    @api.multi
    def print_excel(self):
        data = {}
        return self.env['report'].get_action(self, 'disciplinary_report.xlsx', data=data)