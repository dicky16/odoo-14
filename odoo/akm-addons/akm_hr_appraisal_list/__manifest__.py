# -*- encoding: utf-8 -*-

{
    'name': 'Appraisal List',
    'version': '1.0',
    'category': 'Human Resources/Appraisals',
    'sequence': 180,
    'summary': 'Assess your employees',
    'depends': ['hr', 'calendar', 'akm_employees'],
    "data": [
        'views/hr_appraisal_list.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'application': True,
}
