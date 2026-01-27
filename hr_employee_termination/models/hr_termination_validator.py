# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrTerminationValidator(models.Model):
    _name = 'hr.termination.validator'
    _description = 'Department Clearance Validator'
    _order = "termination_id desc, department_id"

    termination_id = fields.Many2one(
        'hr.employee.termination',
        string='Termination Ref',
        ondelete='cascade'
    )

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help="Departemen yang bertanggung jawab memberikan clearance."
    )

    department_parent_id = fields.Many2one(
        'hr.department',
        related='parent_id.department_id',
        string='Parent Department',
        store=True
    )

    validator_ids = fields.Many2many(
        'hr.employee',
        'termination_validation_employee_rel',
        'termination_validation_id',
        'employee_id',
        string='Authorized Validators'
    )

    validate_employee_id = fields.Many2one(
        'hr.employee',
        string='Validated By',
        readonly=True
    )
    validate_time = fields.Datetime(
        string='Validated Time',
        readonly=True
    )

    state = fields.Selection([
        ('waiting_validation', 'Waiting'),
        ('validate', 'Validated')
    ], default='waiting_validation', string='Status', readonly=True)

    notes = fields.Text(string='Clearance Notes')

    def action_validate(self):
        self.ensure_one()
        user_emp = self.env.user.employee_id

        # Validasi apakah user yang login adalah salah satu dari validator yang ditunjuk
        if not user_emp or user_emp.id not in self.validator_ids.ids:
            raise UserError(
                _("You are not authorized to validate for this department."))

        if self.state == 'validate':
            raise UserError(_("This department has already been validated."))

        return self.write({
            'state': 'validate',
            'validate_employee_id': user_emp.id,
            'validate_time': fields.Datetime.now()
        })
