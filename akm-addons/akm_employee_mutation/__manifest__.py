# -*- coding: utf-8 -*-
{
    'name': 'Employee Mutation',
    'summary': 'Employee Mutation Record and Process',
    'description': 'Employee Mutation Record and Process',
    'version': '1.1.2',
    'category': 'Human Resources',
    'author': 'HashMicro / Kartikeya Gupta',
    'depends': ['hr','hr_contract','akm_employees'],
    'data': [
        'security/employee_mutation_security.xml',
        'security/ir.model.access.csv',
        'views/employee_mutation.xml',
        'data/ir_sequence_data.xml',
        'wizard/renew_contract.xml'
    ],
    'application': True,
    'installable': True,
}
