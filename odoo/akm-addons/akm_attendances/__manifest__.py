{
    'name': 'akm_attendances',
    'version': '1.0',
    'depends': ['hr_attendance', 'akm_employees'],
    'summary': "AKM attendances using ZKTeco face detector",
    'description': """
        AKM attendances using ZKTeco face detector
    """,
    'category': 'hr',
    'data': [
        'views/akm_attendances_view.xml',
        'views/fd_attendances_view.xml',
        #'views/attendance_correction.xml',
        # 'views/hr_flag_sts.xml',
        # 'views/hr_perijinan.xml',
        # 'views/tipe_perijinan.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
