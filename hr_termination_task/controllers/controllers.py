# -*- coding: utf-8 -*-
# from odoo import http


# class HrTerminationTask(http.Controller):
#     @http.route('/hr_termination_task/hr_termination_task', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_termination_task/hr_termination_task/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_termination_task.listing', {
#             'root': '/hr_termination_task/hr_termination_task',
#             'objects': http.request.env['hr_termination_task.hr_termination_task'].search([]),
#         })

#     @http.route('/hr_termination_task/hr_termination_task/objects/<model("hr_termination_task.hr_termination_task"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_termination_task.object', {
#             'object': obj
#         })

