# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

class HrEmployeeTermination(models.Model):
    _name = 'hr.employee.termination'
    _description = 'Employee Termination'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # Odoo 17 Standard: Selection grouping
    RESIGNATION_TYPES = [
        ('RESG', 'Resign'),
        ('TERM', 'Terminate'),
        ('EOCT', 'End Of Contract'),
        ('RETR', 'Retired'),
        ('FRED', 'Fired by the company'),
        ('PSAW', 'Pass Away'),
        ('LOIL', 'Long Illness')
    ]

    name = fields.Char(
        string='Reference', 
        readonly=True, 
        copy=False, 
        index="btree",
        default=lambda self: _('New')
    )
    
    # --- Employee Info ---
    employee_id = fields.Many2one(
        'hr.employee', 
        string="Employee", 
        required=True, 
        tracking=True, 
        index="btree",
        domain="[('active', '=', True)]"
    )
    department_id = fields.Many2one(
        'hr.department', 
        related='employee_id.department_id', 
        store=True, 
        readonly=True
    )
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency', 
        related='company_id.currency_id'
    )

    # --- Dates ---
    letter_issued = fields.Date(
        string='Letter Issued Date', 
        default=fields.Date.context_today, 
        tracking=True
    )
    resignation_date = fields.Date(
        string='Last Working Day', 
        required=True, 
        tracking=True
    )
    effective_date = fields.Date(
        string='Effective Date', 
        required=True, 
        tracking=True
    )
    joined_date = fields.Date(
        string="Join Date", 
        help='Date when employee first joined'
    )

    # --- Termination Details ---
    resignation_type = fields.Selection(
        selection=RESIGNATION_TYPES, 
        string="Termination Type", 
        required=True, 
        tracking=True
    )
    reason = fields.Text(string="Reason Details")
    no_paklaring = fields.Char(string="Certificate No.")
    voc_termination = fields.Html(string='Exit Interview Notes')
    
    # --- Financials ---
    is_penalty = fields.Boolean(string='Has Penalty?')
    penalty_amount = fields.Monetary(
        string='Penalty Amount', 
        currency_field='currency_id'
    )

    # --- State Management ---
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'To Approve'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True, readonly=True)

    # --- Relations ---
    resignation_asset_ids = fields.One2many(
        'hr.termination.asset', 'resignation_id', string='Asset Returns'
    )
    validator_ids = fields.One2many(
        'hr.termination.validator', 'termination_id', string='Department Clearances'
    )
    
    show_validation_button = fields.Boolean(compute='_compute_show_validation_button')

    # --- Logic ---
    @api.constrains('resignation_date', 'effective_date')
    def _check_dates(self):
        for rec in self:
            if rec.resignation_date and rec.effective_date:
                if rec.effective_date < rec.resignation_date:
                    raise ValidationError(_("Effective date cannot be earlier than the last working day."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.employee.termination') or _('New')
        return super().create(vals_list)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Auto-populate assets from Maintenance module."""
        if self.employee_id:
            # Fetch equipment assigned to employee
            equipments = self.env['maintenance.equipment'].search([
                ('employee_id', '=', self.employee_id.id)
            ])
            asset_lines = [(5, 0, 0)] # Clear existing
            for eq in equipments:
                asset_lines.append((0, 0, {
                    'asset_name': eq.name,
                    'serial_no': eq.serial_no,
                    'equipment_id': eq.id,
                }))
            self.resignation_asset_ids = asset_lines

    def action_confirm(self):
        for rec in self:
            rec._create_validator_list()
            rec.write({'state': 'confirm'})

    def _create_validator_list(self):
        self.ensure_one()
        self.validator_ids.unlink()
        vals = []

        # 1. Direct Manager Clearance (Mendukung Lintas Departemen)
        if self.employee_id.parent_id:
            manager = self.employee_id.parent_id
            vals.append((0, 0, {
                # Mengambil departemen milik si Manager, bukan si Employee
                'department_id': manager.department_id.id, 
                'validator_ids': [fields.Command.link(manager.id)],
                'state': 'waiting_validation'
            }))

        # 2. Support Departments (IT, GA, Finance, HC)
        dept_names = ['IT', 'GENERAL AFFAIRS', 'FINANCE', 'HUMAN CAPITAL']
        depts = self.env['hr.department'].search([('name', 'in', dept_names)])
        for dept in depts:
            if dept.manager_id:
                vals.append((0, 0, {
                    'department_id': dept.id,
                    'validator_ids': [fields.Command.link(dept.manager_id.id)],
                    'state': 'waiting_validation'
                }))

        if vals:
            self.validator_ids = vals

    def action_approve(self):
        """Final processing for Odoo 17+."""
        if not self.env.user.has_group('hr.group_hr_manager'):
            raise UserError(_("Only HR Managers can perform final approval."))

        for rec in self:
            if any(v.state != 'validate' for v in rec.validator_ids):
                raise UserError(_("Ensure all department clearances are 'Validated'."))

            # Update Employee Departure (Standard Odoo 17 Fields)
            rec.employee_id.write({
                'active': False,
                'departure_reason': rec.resignation_type,
                'departure_description': rec.reason,
                'departure_date': rec.effective_date,
            })
            
            # Close Contracts
            rec._close_active_contracts()
            rec.write({'state': 'approved'})

    def _close_active_contracts(self):
        self.ensure_one()
        contracts = self.env['hr.contract'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', 'not in', ['close', 'cancel'])
        ])
        contracts.write({
            'date_end': self.resignation_date, 
            'state': 'close'
        })

    @api.depends('state', 'validator_ids.state', 'validator_ids.validator_ids')
    def _compute_show_validation_button(self):
        current_emp = self.env.user.employee_id
        for rec in self:
            if rec.state == 'confirm' and current_emp:
                is_validator = rec.validator_ids.filtered(
                    lambda v: current_emp.id in v.validator_ids.ids and v.state == 'waiting_validation'
                )
                rec.show_validation_button = bool(is_validator)
            else:
                rec.show_validation_button = False