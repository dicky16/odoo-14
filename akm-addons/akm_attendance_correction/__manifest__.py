{
    'name': 'Attendance Correction',
    'version': '1.0',
    'depends': ['hr_attendance','akm_employees','akm_attendance_calendar','hr_work_entry','hr_work_entry_contract','hr_payroll_edit_lines'],
    'summary': "AKM Attendance Payroll",
    'description': """
        Attendance Correction
    """,
    'category': 'HR',
    'data': [
        'views/akm_attendance_view.xml',
        'views/akm_work_entries_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
