{
    'name': 'akm_hr_leave',
    'version': '1.0',
    'depends': ['akm_employees','hr_work_entry','akm_attendances','akm_attendance_correction', 'hr_holidays'],
    'summary': "AKM hr leave",
    'category': 'HR',
    'data': [
        'views/akm_hr_leave.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
