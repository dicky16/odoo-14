{
    'name': 'akm_hr_training',
    'version': '1.0',
    'depends': ['hr'],
    'summary': "AKM hr training",
    'category': 'HR',
    'data': [
        'security/ir.model.access.csv',
        'views/hr_training_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
