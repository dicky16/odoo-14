from odoo import api, fields, models,_
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
import logging
# _logger = logging.getLogger(__name__)

class OvertimeType(models.Model):
	_name = 'overtime.type'

	name = fields.Char('Name', required=1)
	entry_type_id = fields.Many2one('hr.work.entry.type','Work Entry Type')

class OvertimeRequest(models.Model):
	_name = 'overtime.request'
	_inherit = ['mail.thread']

	def _default_type(self):
		type = self.env['overtime.type'].search([],limit=1)
		if type:
			return type

	name = fields.Char('Overtime Reference', required=True, index=True, copy=False, default='New')
	type_id = fields.Many2one('overtime.type','Overtime Type', required=True, default=_default_type)
	entry_type_id = fields.Many2one('hr.work.entry.type','Entry Type', related='type_id.entry_type_id', store=True)
	requester_id = fields.Many2one('hr.employee','Requester', context={'model': 'overtime.request'})
	description = fields.Char('Description')
	date = fields.Date('Date', required=True)
	from_dt = fields.Datetime('From DT')
	to_dt = fields.Datetime('To DT')
	line_ids = fields.One2many('overtime.request.line', 'overtime_id', string='Overtime Lines')
	employee_ids = fields.Many2many('hr.employee')
	state = fields.Selection([
		('draft', 'Draft'),
		('submitted', 'Submitted'),
		('approved', 'Approved'),
		('refused', 'Refused'),
	], default='draft', tracking=True)
	company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company.id)
	note = fields.Char('Notes')

	@api.onchange('date')
	def get_dt(self):
		for x in self:
			today = x.date
			if today:
				x.from_dt = datetime(year=today.year,	month=today.month,day=today.day)-relativedelta(hours=7)
				x.to_dt = datetime(year=today.year,month=today.month,day=today.day, hour=23, minute=59)-relativedelta(hours=7)
			else:
				x.from_dt = False
				x.to_dt = False

	@api.model
	def default_get(self, fields_list):
		self = self.with_context(model='overtime.request')
		res = super(OvertimeRequest, self).default_get(fields_list)
		return res

	@api.depends('name', 'requester_id')
	def name_get(self):
		result = []
		for rec in self:
			name = rec.name
			if rec.requester_id:
				name += ' (' + rec.requester_id.name + ')'
			result.append((rec.id, name))
		return result

	@api.onchange('date_planned')
	def onchange_date_planned(self):
		if self.date_planned:
			self.order_line.filtered(lambda line: not line.display_type).date_planned = self.date_planned

	@api.model
	def create(self, vals):
		company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
		# Ensures default picking type and currency are taken from the right company.
		self_comp = self.with_company(company_id)
		if vals.get('name', 'New') == 'New':
			seq_date = None
			if 'date' in vals:
				seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date']))
			vals['name'] = self_comp.env['ir.sequence'].next_by_code('overtime.request', sequence_date=seq_date) or '/'
		return super(OvertimeRequest, self_comp).create(vals)

	def unlink(self):
		for order in self:
			if not order.state == 'draft':
				raise UserError(_('Only for draft request'))
		return super(OvertimeRequest, self).unlink()

	# @api.multi
	def action_submit(self):
		for rec in self:
			# for x in rec.line_ids:
			# 	if x.entries_id:
			# 		x.entries_id.duration = x.work_hours
			rec.state = 'submitted'

	# @api.multi
	def action_confirm(self):
		for rec in self:
			rec.state = 'approved'

	def action_draft(self):
		for rec in self:
			rec.state = 'draft'

	def action_reject(self):
		self.ensure_one()
		view = self.env.ref('akm_overtime.view_overtime_reject')
		wiz = self.env['overtime.reject'].with_context(active_id=self.id,model='overtime.request').create({})

		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'name': 'Overtime Reject',
			'res_model': 'overtime.reject',
			'context': dict(self._context,),
			'views': [(view.id, 'form')],
			'view_id': view.id,
			'target': 'new',
			'res_id': wiz.id,
		}

class OvertimeRequestLines(models.Model):
	_name = 'overtime.request.line'

	overtime_id = fields.Many2one('overtime.request','Overtime', required=True)
	request_date = fields.Date('Date', related='overtime_id.date', store=True)
	employee_id = fields.Many2one('hr.employee','Employee', required=True, context={'model': 'overtime.request'})
	entries_id = fields.Many2one('hr.work.entry','Work Entry', )
	jumentry = fields.Integer(string='Jum Entry', compute='get_jumentry', store=True)
	pin = fields.Char(string="NIK", related='employee_id.pin', store=True)
	barcode = fields.Char(string="Old NIK", related='employee_id.barcode', store=True)
	pay_location = fields.Many2one('pay.location', string='Pay Loc', related='employee_id.pay_location', store=True)
	pay_group = fields.Many2one('pay.group', string='Pay Group', related='employee_id.pay_group', store=True)
	pay_department = fields.Many2one('pay.department', string='Pay Dept', related='employee_id.pay_department', store=True)
	masuk = fields.Char(string='Masuk', related='entries_id.masuk', store=True)
	keluar = fields.Char(string='Keluar', related='entries_id.keluar', store=True)
	duration = fields.Float(string='Work Hours', related='entries_id.duration', store=True, readonly=False)
	start_time = fields.Float(string='Start Time')
	end_time = fields.Float(string='End Time')
	old_wh = fields.Float(string='Old WH')

	@api.depends('employee_id','request_date')
	def get_jumentry(self):
		for x in self:
			jumen = 0
			if x.employee_id:
				jumens = self.env['hr.work.entry'].search([('employee_id','=',x.employee_id.id),('date_start','>',x.overtime_id.from_dt),('date_start','<',x.overtime_id.to_dt)])
				jumen = len(jumens)
			x.jumentry = jumen

	@api.model
	def default_get(self, fields_list):
		self = self.with_context(model='overtime.request')
		res = super(OvertimeRequestLines, self).default_get(fields_list)
		return res

	def write(self, vals):
		for x in self:
			if vals.get('duration'):
				if vals.get('duration')>x.duration:
					raise ValidationError ("Over work hours")

	@api.onchange('employee_id')
	def onchange_employee(self):
		for x in self:
			if x.overtime_id.date and x.employee_id:
				t= x.overtime_id.date
				start = datetime(t.year, t.month, t.day) - timedelta(hours=7)
				entri = self.env['hr.work.entry'].search([('employee_id','=',x.employee_id.id),('date_start','>=',start)], order='date_start asc', limit=1)
				if entri:
					if entri.overtime_count==0:
						x.entries_id = entri.id
						x.old_wh = x.duration
					else:
						x.old_wh = 0
						raise UserError('Overtime already exist')
				else:
					x.old_wh = 0
		self.get_entries()

	@api.depends('employee_id','overtime_id.date')
	def get_entries(self):
		for x in self:
			if x.overtime_id.date and x.employee_id:
				t= x.overtime_id.date
				start = datetime(t.year, t.month, t.day) - timedelta(hours=7)
				entri = self.env['hr.work.entry'].search([('employee_id','=',x.employee_id.id),('date_start','>=',start)], order='date_start asc', limit=1)
				if entri:
					if entri.overtime_count==0:
						x.entries_id = entri.id
						x.old_wh = x.duration
					else:
						x.old_wh = 0
						raise UserError('Overtime already exist')
				else:
					x.old_wh = 0
