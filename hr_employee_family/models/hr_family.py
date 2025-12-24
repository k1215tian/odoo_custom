from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

FAMILY_SELECTION = [
    ('father', 'Father'),
    ('mother', 'Mother'),
    ('son', 'Son'),
    ('spouse', 'Spouse'),
    ('sister', 'Sister'),
    ('brother', 'Brother'),
    ('daughter', 'Daughter'),
    ('in_law', 'In Law'),
    ('adopted', 'Adopted'),
]

EDUCATION_SELECTION = [
    ('none', 'No Formal Education'),
    ('pre', 'Pre School'),
    ('elementary', 'Elementary'),
    ('junior', 'Junior High School'),
    ('senior', 'Senior High School'),
    ('vocational', 'Vocational School'),
    ('diploma', 'Diploma'),
    ('associate', 'Associate Degree'),
    ('bachelor', 'Bachelor'),
    ('master', 'Master'),
    ('doctoral', 'Doctorate'),
    ('professional', 'Professional Degree'),
    ('under', 'Undergraduate'), # Usually used if degree is incomplete
]

MARITAL_STATUS = [
    ('single', _('Single')),
    ('married', _('Married')),
    ('widower', _('Widower')),
    ('divorced', _('Divorced')),
]


class HRFamily(models.Model):
    _name = 'hr.family'
    _description = 'Employee Family Members'
    _order = 'born_date desc'

    name = fields.Char(string="Full Name", required=True)

    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        ondelete='cascade',
        groups="hr.group_hr_user",
        tracking=True
    )

    is_married = fields.Boolean(
        string='Employee is Married',
        related='employee_id.is_married',
        store=True,  # Storing allows for faster searching/filtering
        groups="hr.group_hr_user",
        tracking=True
    )

    is_self = fields.Boolean(string="Is Self", default=False)
    is_emergency_contact = fields.Boolean(string="Is Emergency Contact", default=False)
    is_spouse = fields.Boolean(string="Is Spouse", default=False)

    phone = fields.Char(string="Phone", default='-')
    job_title = fields.Char(
        string='Job Title',
        groups="hr.group_hr_user",
        tracking=True,
        help="Pekerjaan atau profesi anggota keluarga"
    )
    family_state = fields.Selection(
        FAMILY_SELECTION,
        string='Relationship',
        groups="hr.group_hr_user",
        tracking=True
    )

    last_education = fields.Selection(
        EDUCATION_SELECTION,
        string='Last Education',
        groups="hr.group_hr_user",
        tracking=True
    )

    school_name = fields.Char(
        string='Last School Name',
        groups="hr.group_hr_user",
        tracking=True
    )

    born_date = fields.Date(
        string='Date of Birth',
        groups="hr.group_hr_user",
        tracking=True
    )

    born_at = fields.Integer(
        string='Birth Year',
        compute='_compute_birth_year',
        store=True,
        help="Birth year extracted from Date of Birth"
    )

    place_of_birth = fields.Char(
        'Place of Birth',
        groups="hr.group_hr_user",
        tracking=True
    )

    identification_id = fields.Char(
        string='Identification No',
        groups="hr.group_hr_user",
        tracking=True
    )

    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female')],
        default='male',
        required=True,
        groups="hr.group_hr_user",
        tracking=True
    )

    marital = fields.Selection(
        MARITAL_STATUS,
        string='Marital Status',
        default='single',
        required=True,
        groups="hr.group_hr_user",
        tracking=True
    )

    age = fields.Integer(
        string='Age',
        compute='_compute_age',
        help="Calculated age based on Date of Birth"
    )

    _sql_constraints = [
        ('unique_identification_id',
         'unique(identification_id)',
         'Identification No harus unik! Nomor ini sudah digunakan oleh record lain.')
    ]

    @api.constrains('born_date')
    def _check_born_date(self):
        today = date.today()
        for record in self:
            if record.born_date and record.born_date > today:
                raise ValidationError(_("Tanggal lahir tidak boleh lebih besar dari hari ini!"))

    @api.onchange('family_state')
    def _onchange_family_state_gender(self):
        if self.family_state:
            # Mapping hubungan ke gender tertentu
            male_relations = ['father', 'son', 'brother']
            female_relations = ['mother', 'daughter', 'sister']

            if self.family_state in male_relations:
                self.gender = 'male'
            elif self.family_state in female_relations:
                self.gender = 'female'

    @api.depends('born_date')
    def _compute_age(self):
        today = date.today()
        for record in self:
            if record.born_date:
                dob = record.born_date
                record.age = (
                    today.year - dob.year
                    - ((today.month, today.day) < (dob.month, dob.day))
                )
            else:
                record.age = 0

    @api.depends('born_date')
    def _compute_birth_year(self):
        for record in self:
            record.born_at = record.born_date.year if record.born_date else 0

    @api.constrains('is_self', 'employee_id')
    def _check_unique_self(self):
        for record in self:
            if record.is_self:
                existing = self.search([
                    ('employee_id', '=', record.employee_id.id),
                    ('is_self', '=', True),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(_("Each employee can only have one 'Self' family record."))

    @api.constrains('is_self', 'is_spouse', 'is_emergency_contact')
    def _check_boolean_exclusivity(self):
        for record in self:
            if record.is_self:
                if record.is_spouse:
                    raise ValidationError(_("A record cannot be both 'Self' and 'Spouse'."))
                if record.is_emergency_contact:
                    raise ValidationError(_("You cannot set 'Self' as an Emergency Contact."))

    # UI Logic: Automatically uncheck others when one is selected
    @api.onchange('is_self')
    def _onchange_is_self(self):
        if self.is_self:
            self.is_spouse = False
            self.is_emergency_contact = False

    @api.onchange('is_emergency_contact')
    def _onchange_is_emergency_contact(self):
        if self.is_emergency_contact:
            self.is_self = False
            self.employee_id.emergency_contact = self.name
            self.employee_id.emergency_phone = self.phone

    @api.onchange('is_spouse')
    def _onchange_is_spouse(self):
        for rec in self:
            if rec.is_spouse:
                rec.employee_id.spouse_complete_name = rec.name
                rec.employee_id.spouse_birtdate = rec.birth_date
            else:
                rec.employee_id.spouse_complete_name = False
                rec.employee_id.spouse_birtdate = False