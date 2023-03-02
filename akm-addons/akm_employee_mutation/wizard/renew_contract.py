from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class RenewContractMutation(models.TransientModel):
    _name='renew.contract.mutation'    

    def action_renew_contract(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', [])
        mutation = self.env['employee.mutation'].browse(active_id)
        action = self.env.ref('akm_employee_mutation.act_mutation_contract').read()[0]
        action['views'] = [(self.env.ref('hr_contract.hr_contract_view_form').id, 'form'),(self.env.ref('hr_contract.hr_contract_view_tree').id, 'tree')]
        action['context'] = {'default_employee_id': mutation.employee.id,
                             'default_date_start':mutation.mutation_time,
                             'mutation_id':mutation.id,
                             'default_job_id':mutation.job_position_to_mutation.id,
                             'default_department_id':mutation.department_to_mutation.id,
                             'default_company_id':mutation.company_for_mutation.id,
                             # 'default_work_location':mutation.work_location_mutation,
                             'default_resource_calendar_id':mutation.calendar_to_mutation.id
                            }
        return action