from pkg_resources import require
import re
from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

class HRJob(models.Model):
    _inherit = 'hr.job'

    color = fields.Integer('Color Index')
    code = fields.Char('Job Position Code', size=5)
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', recursive=True, store=True)
    department_id = fields.Many2one('hr.department', string='Department', check_company=True)
    coach_id = fields.Many2one('hr.employee', string='Leader', tracking=True, domain="['|', ('company_id', '=', False), ('company_id', 'in', allowed_company_ids), ('department_id', '=', department_id)]")
    member_ids = fields.One2many('hr.employee', 'department_id', string='Members', readonly=True, domain="['|', ('company_id', '=', False), ('company_id', 'in', allowed_company_ids), ('department_id', '=', department_id)]")
    email = fields.Char(string="Email")
    extent = fields.Char(string="Ext", size=5)
    skills_ids = fields.Many2many('hr.skill', 'hr_skill_job_rel', 'job_id', 'skill_id', string="Skills")

    @api.constrains('email')
    def _check_email_format(self):
        for record in self:
            if record.email:
                # Regex standar untuk validasi format email
                email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                if not re.match(email_pattern, record.email):
                    raise (ValidationError(
                        "Format email '%s' tidak valid! Pastikan menggunakan format yang benar (contoh: nama@perusahaan.com)." % record.email)

    @api.constrains('code'))
    def _check_code_format(self):
        for record in self:
            if record.code:
                if len(record.code) > 5:
                    raise ValidationError(_("Job Position Code tidak boleh lebih dari 5 karakter!"))
                if not re.match(r'^[a-zA-Z0-9]*$', record.code):
                    raise ValidationError(_("Job Position Code hanya boleh berisi karakter Alphanumeric (huruf dan angka)!"))

    @api.constrains('extent')
    def _check_ext_format(self):
        for record in self:
            if record.extent:
                if len(record.extent) > 5:
                    raise ValidationError(_("Code Etension tidak boleh lebih dari 5 karakter!"))
                if not re.match(r'^[0-9]*$', record.extent):
                    raise ValidationError(_("Code Etension hanya boleh berisi karakter Numeric (angka)!"))


    @api.depends('name', 'code')
    def _compute_display_name(self):
        for job in self:
            if job.code:
                job.display_name = f"{job.code} : {job.department_id.name} - {job.name}"
            else:
                job.display_name = job.name

    @api.depends('name', 'code', 'department_id.name')
    def _compute_complete_name(self):
        for job in self:
            if job.code and job.department_id:
                job.complete_name = f"[{job.code}] {job.department_id.name} - {job.name}"
            elif job.department_id:
                job.complete_name = f"{job.department_id.name} - {job.name}"
            else:
                job.complete_name = job.name

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=100, order=None):
        domain = domain or []
        if name:
            name_domain = [
                '|', '|',
                ('code', operator, name),
                ('name', operator, name),
                ('department_id.name', operator, name)
            ]
            domain = name_domain + domain
        return self._search(domain, limit=limit, order=order)