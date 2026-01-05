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
    employee_id = fields.Many2one('hr.employee', string='Employee')
    education_id = fields.Many2one('hr.education', string='Education')
    # Fixed the Many2many definition
    skill_ids = fields.Many2many(
        'hr.skill',
        'hr_certification_skills_rel',
        'certification_id',
        'skill_id',
        string='Skills'
    )
