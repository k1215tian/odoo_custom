# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrEducation(models.Model):
    _name = 'hr.education'
    _description = 'HrEducation'

    name = fields.Char('Name', required=True, index=True)
    is_formal = fields.Boolean('Is Formal Education')
    employee_id = fields.Many2one('hr.employee', string='Employee')
