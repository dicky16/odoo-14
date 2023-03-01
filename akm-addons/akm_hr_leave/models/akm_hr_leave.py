from odoo import fields, models, api
from datetime import datetime, timedelta


class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    is_leave = fields.Boolean(string="Cuti", compute="_compute_is_leave")

    @api.depends("work_entry_type_id")
    def _compute_is_leave(self):
        for x in self:
            x.is_leave = False
            if x.work_entry_type_id:
                result = True if x.work_entry_type_id.code == "IM" or x.work_entry_type_id.code == "CT" else False
                x.is_leave = result

    @api.onchange("work_entry_type_id")
    def onchange_flag_sts(self):
        for x in self:
            is_exist = self.env['hr.leave'].search_count([('work_entry_id', '=', x._origin.id)])
            date_from = datetime.strptime(x.actual_date.strip() + " " + x.sched_in, "%d-%m-%Y %H:%M:%S")
            date_to = datetime.strptime(x.actual_date.strip() + " " + x.sched_out, "%d-%m-%Y %H:%M:%S")
            req_date = str(date_from.strftime("%Y-%m-%d"))
            we_type = x.work_entry_type_id.id
            type = self.env['hr.leave.type'].search([('work_entry_type_id', '=', we_type)],order="id desc",limit=1)
            if x.work_entry_type_id.code == 'IM' and is_exist == 0 and x.actual_date:
                self.env['hr.leave'].create({
                    "holiday_status_id": type.id,
                    "employee_id": x.employee_id.id,
                    "date_from": date_from - timedelta(hours=7),
                    "date_to": date_to - timedelta(hours=7),
                    "work_entry_id": x._origin.id,
                    "request_date_from": req_date,
                    "request_date_to": req_date,
                })
            elif x.work_entry_type_id.code == 'CT' and is_exist == 0 and x.actual_date:
                self.env['hr.leave'].create({
                    "holiday_status_id": type.id,
                    "employee_id": x.employee_id.id,
                    "date_from": date_from - timedelta(hours=7),
                    "date_to": date_to - timedelta(hours=7),
                    "work_entry_id": x._origin.id,
                    "request_date_from": req_date,
                    "request_date_to": req_date,
                })


    def action_view_cuti(self):
        self.ensure_one()
        action = self.env.ref("hr_holidays.hr_leave_action_action_approve_department")
        result = action.read()[0]
        over = self.env['hr.leave'].search([
            ('employee_id', '=', self.employee_id.id),
            ('work_entry_id', '=', self.id)
        ])
        result["domain"] = [("id", "in", over.ids)]
        result['context'] = [{'search_default_managed_people': 0, 'hide_employee_name': 1}]
        return result


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    work_entry_id = fields.Many2one('hr.work.entry', string="Work Entry ID")
    request_date_from = fields.Date('Request Start Date', compute="_compute_date_from")
    request_date_to = fields.Date('Request End Date')
    leave_type = fields.Integer(string="Leave Type", compute="_compute_leave_type")
    holiday_status_id = fields.Many2one('hr.leave.type',
                                        string='Leave Type',
                                        required=True)

    @api.depends("work_entry_id")
    def _compute_leave_type(self):
        for x in self:
            if x.work_entry_id:
                x.leave_type = x.work_entry_id.work_entry_type_id.id

    @api.depends("work_entry_id")
    def _compute_date_from(self):
        for x in self:
            date_from = str(x.date_from + timedelta(hours=7))[:10]
            date_to = str(x.date_to + timedelta(hours=7))[:10]
            x.request_date_from = date_from
            x.request_date_to = date_to
            x.state = 'validate'

    def _check_date_state(self):
        super(HrLeave, self)._check_date_state()
        for holiday in self:
            if holiday.state in ['cancel', 'refuse', 'validate1']:
                raise ValidationError(_("This modification is not allowed in the current state."))
                
class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    work_entry_type_id = fields.Many2one('hr.work.entry.type', string="Work Entry Type")
