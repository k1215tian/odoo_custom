from odoo import fields, models, api


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    termination_count = fields.Integer(compute='_compute_termination_count')

    def _compute_termination_count(self):
        for rec in self:
            rec.termination_count = self.env['hr.employee.termination'].search_count([('employee_id', '=', rec.id)])

    def action_open_termination(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Termination Record',
            'res_model': 'hr.employee.termination',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
        }