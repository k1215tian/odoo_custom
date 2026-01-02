# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class TrasnportRoute(models.Model):
    _name = 'trasnport.route'
    _description = 'TrasnportRoute'

    name = fields.Char('Name')
