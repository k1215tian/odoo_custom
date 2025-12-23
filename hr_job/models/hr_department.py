import re # Import library regex untuk validasi format
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class HRDepartment(models.Model):
    _inherit = 'hr.department'

    code = fields.Char('Department Code',size=5)
    email = fields.Char(string="Email")

    @api.constrains('email')
    def _check_email_format(self):
        for record in self:
            if record.email:
                # Regex standar untuk validasi format email
                email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                if not re.match(email_pattern, record.email):
                    raise ValidationError(
                        "Format email '%s' tidak valid! Pastikan menggunakan format yang benar (contoh: nama@perusahaan.com)." % record.email)

    @api.constrains('code')
    def _check_code_format(self):
        for record in self:
            if record.code:
                if len(record.code) > 5:
                    raise ValidationError(_("Job Position Code tidak boleh lebih dari 5 karakter!"))
                if not re.match(r'^[a-zA-Z0-9]*$', record.code):
                    raise ValidationError(_("Job Position Code hanya boleh berisi karakter Alphanumeric (huruf dan angka)!"))

    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        if not self._check_recursion():
            raise ValidationError(
                _('You cannot create recursive departments. A department cannot be its own parent or a descendant of itself.'))

    @api.depends_context('hierarchical_naming')
    def _compute_display_name(self):
        if self.env.context.get('hierarchical_naming', True):
            return super()._compute_display_name()
        for record in self:
            current_code = record.code or ""
            name = record.name or ""
            if record.parent_id and record.parent_id.code:
                parent_code = record.parent_id.code
                record.display_name = f"{parent_code} - {current_code} : {name}"
            elif current_code:
                record.display_name = f"{current_code} : {name}"
            else:
                record.display_name = name

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for department in self:
            if department.parent_id:
                department.complete_name = '%s / %s' % (department.parent_id.complete_name, department.name)
            else:
                department.complete_name = department.name

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            # Mencari berdasarkan Code ATAU Name
            domain = ['|', '|', ('code', operator, name), ('name', operator, name), ('display_name', operator, name), ('complete_name', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)