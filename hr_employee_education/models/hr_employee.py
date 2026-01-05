# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    certification_ids = fields.One2many(
        'hr.certification', 'employee_id', string='Certifications')
    education_ids = fields.One2many(
        'hr.education', 'employee_id', string='Educations')
