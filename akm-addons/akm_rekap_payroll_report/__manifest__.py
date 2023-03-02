# -- coding: utf-8 --
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2019. All rights reserved.

{
    'name': 'Rekap Payroll Report',
    'version': '14.0.0.0',
    'sequence': 1,
    'category': 'HR',
    'summary': 'Rekap Payroll Report xlsx',
    'author': 'Yustaf Pramsistya',
    'website': 'http://www.alugarainovasi.com/',
    'price': 80,
    'currency': 'USD',
    'license': 'Other proprietary',
    'description': """Rekap Payroll Report xlsx
        """,
    'depends': ['hr_payroll','akm_premi'],
    'data': [
        # 'report/absensi_hl_report.xml',
        'wizard/rekap_payroll_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
