{
    'name': 'HR Premi Kehadiran',
    'author': 'Alugara Inovasi Utama',
    'description': '',
    'summary': '',
    'depends': ['hr_payroll', 'hr', 'hr_work_entry_contract','akm_employees'],
    'data': [
        'views/settings_views.xml',
        'views/hr_payslip_views.xml',
        'views/employee_views.xml',
        'wizard/hr_generate_payslip_views.xml',
        'data/hr_salary_rule_data.xml',
        'security/ir.model.access.csv',
    ]
}
