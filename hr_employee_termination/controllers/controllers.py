# -*- coding: utf-8 -*-
# from odoo import http


# class HrEmployeeTermination(http.Controller):
#     @http.route('/hr_employee_termination/hr_employee_termination', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_employee_termination/hr_employee_termination/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_employee_termination.listing', {
#             'root': '/hr_employee_termination/hr_employee_termination',
#             'objects': http.request.env['hr_employee_termination.hr_employee_termination'].search([]),
#         })

#     @http.route('/hr_employee_termination/hr_employee_termination/objects/<model("hr_employee_termination.hr_employee_termination"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_employee_termination.object', {
#             'object': obj
#         })

