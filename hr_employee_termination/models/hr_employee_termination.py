# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrEmployeeTermination(models.Model):
    """ This model represents hr.employee.termination."""
    _name = 'hr.employee.termination'
    _description = 'HrEmployeeTermination'

    name = fields.Char(string='Customer Name', required=True)
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals):
        """Override the default create method to customize record creation logic."""
        return super().create(vals)