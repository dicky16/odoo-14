# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'HR Menu Arrange',
    'version': '0.1',
    'category': 'Tools',
    'depends': ['base','hr','hr_work_entry_contract','hr_attendance','hr_holidays', 'hr_contract','akm_employees','akm_attendances','akm_perijinan', 'akm_overtime'],
    'data': [
        'security/security.xml',
        'data/menus_arrange.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
