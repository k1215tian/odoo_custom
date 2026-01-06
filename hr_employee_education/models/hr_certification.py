# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrCertification(models.Model):
    _name = 'hr.certification'
    _description = 'HrCertification'

    name = fields.Char('Name', required=True, index=True)
    is_formal = fields.Boolean('Is Formal Education')
    is_profesion = fields.Boolean('Is Profesional Certification')
    use_validity_period = fields.Boolean(
        string='Menggunakan Masa Berlaku',
        help='Centang jika sertifikat memiliki masa berlaku'
    )
    employee_id = fields.Many2one('hr.employee', string='Employee')
    education_id = fields.Many2one('hr.education', string='Education')
    skill_ids = fields.Many2many(
        'hr.skill',
        'hr_certification_skills_rel',
        'certification_id',
        'skill_id',
        string='Skills'
    )
    institution = fields.Char(string='Institusi/Sekolah', required=True)
    releaase_date = fields.Date(string='Released Date', required=True)
    start_date = fields.Date(string='Issue Date', required=True)
    end_date = fields.Date(string='Expiry Date',
                           help="Kosongkan jika berlaku selamanya")
    description = fields.Text(string='Keterangan')

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(
                    _("Tanggal mulai tidak boleh lebih besar dari tanggal lulus/selesai."))
