# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class hr_termination_task(models.Model):
#     _name = 'hr_termination_task.hr_termination_task'
#     _description = 'hr_termination_task.hr_termination_task'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

