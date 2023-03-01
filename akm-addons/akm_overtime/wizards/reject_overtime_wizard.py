
from odoo import models, fields, api

class OvertimeWizard(models.TransientModel):
	_name = 'overtime.reject'
	_description = 'Overtime Reject Wizard'

	note = fields.Text('Note')
	request_id = fields.Many2one('overtime.request', string='Request')

	@api.model
	def default_get(self, fields):
		res = super(OvertimeWizard, self).default_get(fields)
		context = dict(self._context or {})
		active_id = context.get('active_id', [])
		if context.get('model', False)=='overtime.request':
			request = self.env['overtime.request'].browse(active_id)
			res['request_id'] = request.id or False

		return res

	def confirm_button(self):
		self.ensure_one()
		if self.note:
			self.request_id.state = 'refused'
			self.request_id.note = self.note