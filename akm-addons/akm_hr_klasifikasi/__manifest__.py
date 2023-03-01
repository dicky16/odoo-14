{
    'name': 'akm_hr_klasifikasi',
    'version': '1.0',
    'depends': ['akm_hr_appraisal'],
    'summary': "AKM hr klasifikasi appraisal",
    'category': 'HR',
    'data': [
        'security/ir.model.access.csv',
        'views/hr_klasifikasi.xml',
        'views/hr_appraisal_type.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
