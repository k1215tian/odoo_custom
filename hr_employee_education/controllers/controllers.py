# -*- coding: utf-8 -*-
# from odoo import http


# class HrEmployeeEducation(http.Controller):
#     @http.route('/hr_employee_education/hr_employee_education', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_employee_education/hr_employee_education/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_employee_education.listing', {
#             'root': '/hr_employee_education/hr_employee_education',
#             'objects': http.request.env['hr_employee_education.hr_employee_education'].search([]),
#         })

#     @http.route('/hr_employee_education/hr_employee_education/objects/<model("hr_employee_education.hr_employee_education"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_employee_education.object', {
#             'object': obj
#         })

