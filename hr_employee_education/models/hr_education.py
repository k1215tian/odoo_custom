# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

EDUCATION_SELECTION = [
    ('junior', 'Junior High School'),
    ('senior', 'Senior High School'),
    ('vocational', 'Vocational School'),
    ('diploma', 'Diploma'),
    ('associate', 'Associate Degree'),
    ('bachelor', 'Bachelor'),
    ('master', 'Master'),
    ('doctoral', 'Doctorate'),
    ('professional', 'Professional Degree'),
    ('course', 'Course/Training'),  # Tambahan untuk non-formal
]


class HrEducation(models.Model):
    _name = 'hr.education'
    _description = 'HR Education'

    name = fields.Char('Name', required=True, index=True)
    is_formal = fields.Boolean('Is Formal Education')
    is_certification = fields.Boolean('Is Certification Relase')
    certification_no = fields.Char(string='Certification No.')
    certification_id = fields.Many2one(
        'hr.certification', string='Certification.')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    level = fields.Selection(
        EDUCATION_SELECTION, string='Level', required=True)
    degree_title = fields.Char(
        string='Gelar/Title', help="Contoh: S.T., M.Kom, atau Certified Scrum Master")
    institution = fields.Char(string='Institusi/Sekolah', required=True)
    major = fields.Char(string='Jurusan/Bidang Studi')
    start_date = fields.Date(string='Tanggal Mulai', required=True)
    end_date = fields.Date(string='Tanggal Lulus/Selesai', required=True)
    description = fields.Text(string='Keterangan')
    skill_ids = fields.Many2many(
        'hr.skill',
        'hr_certification_skills_rel',
        'certification_id',
        'skill_id',
        string='Skills'
    )
    use_validity_period = fields.Boolean(
        string='Menggunakan Masa Berlaku untuk ijazah/sertifikat',
        help='Centang jika sertifikat memiliki masa berlaku ijazah/sertifikat',
    )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(
                    _("Tanggal mulai tidak boleh lebih besar dari tanggal lulus/selesai."))

    def action_generate_certification(self):
        self.ensure_one()

        # Validasi: Pastikan end_date pendidikan sudah diisi sebelum generate sertifikat
        if not self.end_date:
            raise UserError(
                _("Harap isi Tanggal Lulus/Selesai terlebih dahulu sebagai acuan tanggal terbit sertifikat."))

        existing_cert = self.env['hr.certification'].search(
            [('education_id', '=', self.id)], limit=1)
        if existing_cert:
            raise UserError(
                _("Sertifikat untuk pendidikan ini sudah pernah dibuat."))

        cert_vals = {
            'name': f"Sertifikat/Ijazah: {self.name}",
            'education_id': self.id,
            'employee_id': self.employee_id.id,
            'institution': self.institution,
            # Menggunakan end_date pendidikan sebagai Issue Date sertifikat
            'releaase_date': self.end_date,
            'start_date': self.end_date,
            'description': self.description,
            'is_formal': self.is_formal,
            'skill_ids': [(6, 0, self.skill_ids.ids)],
            'use_validity_period': self.use_validity_period,
        }

        new_cert = self.env['hr.certification'].create(cert_vals)
        self.write({'certification_id': new_cert.id})

        return {
            'name': _('Certification'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.certification',
            'res_id': new_cert.id,
            'view_mode': 'form',
            'target': 'current',
        }
