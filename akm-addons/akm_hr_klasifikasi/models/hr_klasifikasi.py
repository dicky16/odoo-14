from odoo import models, fields, api


class HrPaLevel(models.Model):
    _name = "hr.palevel"

    name = fields.Char("Name")


class HrAppraisalTipe(models.Model):
    _name = "hr.appraisal.type"

    name = fields.Char("Name")


class HrAppraisal(models.Model):
    _inherit = "hr.appraisal"

    periode_1 = fields.Float(string="Periode 1")
    periode_2 = fields.Float(string="Periode 2")
    periode_3 = fields.Float(string="Periode 3")
    periode_4 = fields.Float(string="Periode 4")
    periode_5 = fields.Float(string="Periode 5")
    periode_6 = fields.Float(string="Periode 6")
    pa_level = fields.Many2one("hr.palevel", string="PA Level")
    appraisal_type = fields.Many2one("hr.appraisal.type", string="Appraisal Type")
    barcode = fields.Char(string='Old NIK', related="employee_id.barcode")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    month_periode = fields.Integer(string="Month Periode", compute="_compute_month_periode", store=True)
    is_period = fields.Boolean(string="Is Period")
    score_number = fields.Float(string="Score")
    note = fields.Char(string="Note")

    @api.onchange("appraisal_type")
    def onchange_appraisal_type(self):
        for x in self:
            if x.appraisal_type.name == "PA Tahunan":
                x.is_period = False
            elif x.appraisal_type.name == "Penilaian Masa Kerja":
                x.is_period = True

    @api.depends("score_number")
    def _compute_month_periode(self):
        for x in self:
            if x.periode2:
                year = int(x.periode2[0]) * 12
                month = int(x.periode2[9])
                x.month_periode = year + month

    @api.onchange("score_number", "pa_level", "appraisal_type")
    def onchange_score_number(self):
        for x in self:
            if x.pa_level.name == 'Managerial':
                if x.is_period:
                    if x.score_number >= 38 and x.score_number <= 60:
                        x.assessment_note = self.env['hr.appraisal.note'].search([("code", "=", "I")]).id
                    elif x.score_number >= 0 and x.score_number <= 37.9:
                        x.assessment_note = self.env['hr.appraisal.note'].search([("code", "=", "II")]).id
                else:
                    if x.score_number >= 59 and x.score_number <= 68:
                        x.assessment_note = self.env['hr.appraisal.note'].search([("code", "=", "A")]).id
                    elif x.score_number >= 47 and x.score_number <= 58:
                        x.assessment_note = self.env['hr.appraisal.note'].search([("code", "=", "B")]).id
                    elif x.score_number >= 34 and x.score_number <= 46:
                        x.assessment_note = self.env['hr.appraisal.note'].search([("code", "=", "C")]).id
                    elif x.score_number < 34:
                        x.assessment_note = self.env['hr.appraisal.note'].search([("code", "=", "D")]).id
            elif x.pa_level.name == 'Non Managerial':
                if x.is_period:
                    if x.score_number >= 28.0 and x.score_number <= 44:
                        x.assessment_note = self.env['hr.appraisal.note'].search([("code", "=", "I")]).id
                    elif x.score_number >= 0 and x.score_number <= 27.9:
                        x.assessment_note = self.env['hr.appraisal.note'].search([("code", "=", "II")]).id
                else:
                    if x.score_number >= 42 and x.score_number <= 48:
                        x.assessment_note = self.env['hr.appraisal.note'].search([("code", "=", "A")]).id
                    elif x.score_number >= 33 and x.score_number <= 41:
                        x.assessment_note = self.env['hr.appraisal.note'].search([("code", "=", "B")]).id
                    elif x.score_number >= 24 and x.score_number <= 32:
                        x.assessment_note = self.env['hr.appraisal.note'].search([("code", "=", "C")]).id
                    elif x.score_number < 24:
                        x.assessment_note = self.env['hr.appraisal.note'].search([("code", "=", "D")]).id

    @api.onchange('periode_1', 'periode_2', 'periode_3', 'periode_4', 'periode_5', 'periode_6', 'pa_level',"appraisal_type")
    def klasifikasi_nilai(self):
        for x in self:
            count = [x.periode_1, x.periode_2, x.periode_3, x.periode_4, x.periode_5, x.periode_6]
            total = 0
            result = 0
            if x.is_period:
                for i in count:
                    if i != 0:
                        total += 1
                        result += i
                if total:
                    x.score_number = result / total
            else:
                for i in count:
                    i = 0

