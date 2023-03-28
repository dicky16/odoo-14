{
    'name': 'akm_perijinan',
    'version': '1.0',
    'depends': ['hr_attendance', 'akm_employees'],
    'summary': "AKM perijinan",
    'description': """
        AKM perijinan
    """,
    'category': 'hr',
    'data': [
        'views/hr_perijinan.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
