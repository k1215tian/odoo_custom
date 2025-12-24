from odoo import fields, models, api


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    @api.onchange('job_id','coach_id')
    def _onchange_job_id(self):
        for line in self:
            if line.job_id:
                if not line.job_title:
                    line.job_title = line.job_id.name
                if line.job_id.coach_id and not line.coach_id:
                    line.coach_id = line.job_id.coach_id.id

