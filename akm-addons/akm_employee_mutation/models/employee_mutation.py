from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class EmployeeMutation(models.Model):
    _name='employee.mutation'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('employee.mutation') or _('New')
            date = datetime.strptime(vals['mutation_time'], "%Y-%m-%d")
            year = date.year

            vals['name']="MUT"+str(year)[-2:]+'-'+str(vals['name'])[-4:]
        result = super(EmployeeMutation, self).create(vals)
        contract = self.env['hr.contract'].search([('employee_id', '=', result.employee.id)])
        result.contract_count=len(contract)
        return result

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    employee = fields.Many2one('hr.employee')
    mutation_time = fields.Date('Mutation Date',default=fields.Date.context_today)

    pay_group = fields.Many2one('pay.group', string='Pay Group', store=True)
    pay_department = fields.Many2one('pay.department', string='Pay Department', store=True)
    pay_location = fields.Many2one('pay.location', string='Pay Location', store=True)

    company = fields.Many2one('res.company',string="Company", store=True)
    grade = fields.Selection(string='Grade', related='employee.grade', store=True)
    job_position = fields.Many2one('hr.job',string= "Job Position", store=True)
    work_location = fields.Char('Work Location', store=True)
    department = fields.Many2one('hr.department',string='Department', store=True)
    sub_department = fields.Many2one('hr.department',string='Sub Department', store=True)
    section = fields.Many2one('hr.department',string='Section', store=True)
    resource_calendar_id = fields.Many2one('resource.calendar', string="Shift", store=True)

    company_for_mutation = fields.Many2one('res.company',string="To Company")
    job_position_to_mutation = fields.Many2one('hr.job',string="To Position")
    department_to_mutation = fields.Many2one('hr.department',string="To Department",
                                     domain="[('grade', '=', 'department')]")
    sub_department_to_mutation = fields.Many2one('hr.department',string="To Sub Department",
                                     domain="[('grade', '=', 'sub_department')]")
    section_to_mutation = fields.Many2one('hr.department',string='To Section',
                                     domain="[('grade', '=', 'section')]")
    location_to_mutation = fields.Many2one('pay.location',string="To Pay Location", required=True)
    calendar_to_mutation = fields.Many2one('resource.calendar', string="To Shift")
    pay_group_to_mutation = fields.Many2one("pay.group", string="Pay Group")
    pay_department_to_mutation = fields.Many2one("pay.department", string="Pay Department")
    pin = fields.Char(string="NIK", related="employee.pin")
    barcode = fields.Char(string='Old NIK', related="employee.barcode")


    state = fields.Selection([
        ('draft','Draft'),
        ('waiting','Waiting Approval'),
        ('approved','Approved'),
        ('rejected','Rejected'),
        ('renew_contracts','Renew Contract')],string="State",default='draft')
    contract_count = fields.Integer()
    description = fields.Text(string="Notes")

    @api.model
    def default_get(self, fields):
        rec = super(EmployeeMutation, self).default_get(fields)
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if employee_id:
            rec['employee'] = employee_id and employee_id.id or False
        return rec
    
    
    @api.onchange('employee')
    def onchange_employee(self):
        if self.employee:
            self.company = self.employee.company_id.id
            self.pay_department = self.employee.pay_department.id
            self.pay_location = self.employee.pay_location.id
            self.pay_group = self.employee.pay_group.id
            self.job_position = self.employee.job_id.id
            self.work_location = self.employee.work_location
            self.department = self.employee.department_id.id
            self.sub_department = self.employee.sub_department.id
            self.section = self.employee.section.id
            self.resource_calendar_id = self.employee.resource_calendar_id.id

            self.company_for_mutation = self.employee.company_id.id
            self.job_position_to_mutation = self.employee.job_id.id
            # self.location_to_mutation = self.employee.work_location
            self.department_to_mutation = self.employee.department_id.id
            self.sub_department_to_mutation = self.employee.sub_department.id
            self.section_to_mutation = self.employee.section.id
            self.calendar_to_mutation = self.employee.resource_calendar_id.id
            self.pay_department_to_mutation = self.employee.pay_department.id
            self.pay_group_to_mutation = self.employee.pay_group.id
            self.location_to_mutation = self.employee.pay_location


    def submit(self):
        self.state='waiting'

    def action_approve12(self):
        self.env['hr.employee'].search([
            ('id', '=', self.employee.id)
        ]).write({
            'pay_department': self.pay_department_to_mutation.id,
            'pay_group': self.pay_group_to_mutation.id,
            'department_id': self.department_to_mutation.id,
            'sub_department': self.sub_department_to_mutation.id,
            'section': self.section_to_mutation.id,
            'pay_location': self.location_to_mutation.id,
            'job_id': self.job_position_to_mutation.id,
            'resource_calendar_id': self.calendar_to_mutation.id,
        })
        self.state='approved' 

    def action_reject(self):
        self.state='rejected'

    @api.onchange('company_for_mutation')
    def change_company_for_mutation(self):
        self.job_position_to_mutation=False
        # self.work_location_mutation=False

    # @api.multi
    def action_view_contracts(self):
        contracts = self.env['hr.contract'].search([('employee_id', '=', self.employee.id)])
        if self.state == 'approved':
            for rec in contracts:
                if rec.date_end:
                    if self.mutation_time < rec.date_end:
                        rec.state = 'close'
        action = self.env.ref('akm_employee_mutation.act_mutation_contract').read()[0]
        self.contract_count = len(contracts)

        action['domain'] = [('employee_id', '=', self.employee.id)]
        return action    


    # @api.multi
    def action_renew_contract(self):  
        
        action = self.env.ref('akm_employee_mutation.renew_contract_wizard_action_mutation').read()[0]
        return action   

class HrContractEmployeeMutation(models.Model):
    _inherit='hr.contract'
    
    @api.model
    def create(self, vals):
        result = super(HrContractEmployeeMutation, self).create(vals)
        context = dict(self._context or {})
        
        active_id = context.get('mutation_id', [])
        mutation = self.env['employee.mutation'].browse(active_id)
        if mutation:
            mutation.state = 'renew_contracts'
            mutation.contract_count +=1
        contract = self.env['hr.contract'].search([('employee_id', '=', mutation.employee.id),('id','!=',result.id)])
        for rec in contract:
            result.wage = rec.wage
            if result.structure_type_id:
                result.structure_type_id = rec.structure_type_id
            if result.hr_responsible_id:
                result.hr_responsible_id = rec.hr_responsible_id
            rec.state = 'close'
        
        if mutation.job_position_to_mutation:
            result.employee_id.job_id = mutation.job_position_to_mutation.id
        if mutation.location_to_mutation:
            result.employee_id.work_location = mutation.location_to_mutation

        if mutation.department_to_mutation:
            result.employee_id.department_id = mutation.department_to_mutation.id
        if mutation.sub_department_to_mutation:
            result.employee_id.sub_department = mutation.sub_department_to_mutation.id
        if mutation.section_to_mutation:
            result.employee_id.section = mutation.section_to_mutation.id

        # if result.department_id:
        #     result.employee_id.department_id = result.department_id.id
        if result.company_id:
            result.employee_id.company_id = result.company_id.id
        if result.resource_calendar_id:
            result.employee_id.resource_calendar_id = result.resource_calendar_id.id

        return result

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    mutation_history_ids = fields.One2many('employee.mutation', 'employee')
