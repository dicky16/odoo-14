{
    'name': 'akm_employees',
    'version': '1.0',
    'depends': ['hr'],
    'summary': "AKM employees",
    'description': """
        Employee customize information
    """,
    'category': 'HR',
    'data': [
        'data/program_tk_data.xml',
        'security/ir.model.access.csv',
        'views/akm_employee_views.xml',
        'views/master_views.xml',
        'views/akm_bpjs.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
