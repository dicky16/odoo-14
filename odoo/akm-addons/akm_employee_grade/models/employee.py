from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from random import randint

class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    grade_id = fields.Many2one('hr.grade', string='Grade')
    grade = fields.Selection(string='Grade', related='grade_id.type',store=True)
    facility_ids = fields.Many2many('hr.grade.facility', string='Facilities', related='grade_id.facility_ids')

class Department(models.Model):
    _inherit = 'hr.department'

    grade_id = fields.Many2one('hr.grade', string='Grade')
    grade = fields.Selection(string='Grade', related='grade_id.type',store=True)

class HrEmployeeGrade(models.Model):
    _description = 'Employee Grade'
    _name = "hr.grade"
    _order = 'sequence, name'

    def _default_facility(self):
        return self.env['hr.grade.facility'].browse(self._context.get('facility_id'))

    sequence = fields.Integer(string='Seq', default=1, required=1)
    name = fields.Char(string='Name', required=1)
    type = fields.Selection([
        ('director', 'Director'),
        ('division', 'Division'),
        ('department', 'Department'),
        ('sub_department', 'Sub Department'),
        ('section', 'Section'),
        ('non', 'Non Managerial')], string='Type', required=True)
    salary_structure_ids = fields.Many2many('hr.payroll.structure.type', column1='grade_id',
                                            column2='structure_id', string='Salary Structures')
    # facility_ids = fields.One2many('hr.grade.facility','grade_id', string='Facilities')
    facility_ids = fields.Many2many('hr.grade.facility', column1='grade_id', string='Facilities',
                                    column2='facility_id', default=_default_facility)

    def name_get(self):
        res = []
        for rec in self:
            name = "%s. %s" % (rec.sequence, rec.name)
            res += [(rec.id, name)]
        return res

class GradeFacility(models.Model):
    _description = 'Grade Facilities'
    _name = 'hr.grade.facility'
    _order = 'name'
    _parent_store = True

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Name', required=True, translate=True)
    color = fields.Integer(string='Color Index', default=_get_default_color)
    parent_id = fields.Many2one('hr.grade.facility', string='Parent Category', index=True, ondelete='cascade')
    child_ids = fields.One2many('hr.grade.facility', 'parent_id', string='Child Tags')
    active = fields.Boolean(default=True, help="The active field allows you to hide the category without removing it.")
    parent_path = fields.Char(index=True)
    grade_ids = fields.Many2many('hr.grade', column1='facility_id', column2='grade_id', string='Grade')

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('You can not create recursive tags.'))

    def name_get(self):
        """ Return the categories' display name, including their direct
            parent by default.

            If ``context['partner_category_display']`` is ``'short'``, the short
            version of the category name (without the direct parent) is used.
            The default is the long version.
        """
        if self._context.get('grade_facility_display') == 'short':
            return super(GradeFacility, self).name_get()

        res = []
        for facility in self:
            names = []
            current = facility
            while current:
                names.append(current.name)
                current = current.parent_id
            res.append((facility.id, ' / '.join(reversed(names))))
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            args = [('name', operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)