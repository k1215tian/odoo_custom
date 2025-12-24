from odoo import fields, models, api


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    family_ids = fields.One2many('hr.family','employee_id',string='Family')
    is_married = fields.Boolean('Married State', default=False,groups="hr.group_hr_user", tracking=True)
    date_marriage = fields.Date(
        string='Marriage Date',
        groups="hr.group_hr_user",
        help="Date of marriage for benefit eligibility"
    )
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], groups="hr.group_hr_user", tracking=True)

    @api.onchange('marital') # 'marital' is the native Odoo field
    def _onchange_marital_status(self):
        if self.marital != 'married':
            self.date_marriage = False
            self.is_married = False
        else:
            self.is_married = True