# -- coding: utf-8 --
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2019. All rights reserved.

{
    'name': 'Absensi HL Report',
    'version': '14.0.0.0',
    'sequence': 1,
    'category': 'HR',
    'summary': 'Absensi HL Report xlsx',
    'author': 'Yustaf Pramsistya',
    'website': 'http://www.alugarainovasi.com/',
    'price': 80,
    'currency': 'USD',
    'license': 'Other proprietary',
    'description': """Absensi HL Report xlsx
        """,
    'depends': ['akm_attendance_correction','akm_employees','akm_attendance_calendar'],
    'data': [
        'report/absensi_hl_report.xml',
        'wizard/absensi_hl_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
