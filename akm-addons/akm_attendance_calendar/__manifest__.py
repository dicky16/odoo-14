{
    'name': 'Attendance Calendar',
    'version': '1.0',
    'depends': ['hr_attendance', 'hr_payroll','akm_employees'],
    'summary': "AKM Calendar Rest Time",
    'description': """
        AKM Calendar
    """,
    'category': 'HR',
    'data': [
        # 'views/akm_attendance_view.xml',
        'views/resource_calendar_attendance.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
