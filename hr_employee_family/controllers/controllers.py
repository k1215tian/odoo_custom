# -*- coding: utf-8 -*-
# from odoo import http


# class HrEmployeeFamily(http.Controller):
#     @http.route('/hr_employee_family/hr_employee_family', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_employee_family/hr_employee_family/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_employee_family.listing', {
#             'root': '/hr_employee_family/hr_employee_family',
#             'objects': http.request.env['hr_employee_family.hr_employee_family'].search([]),
#         })

#     @http.route('/hr_employee_family/hr_employee_family/objects/<model("hr_employee_family.hr_employee_family"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_employee_family.object', {
#             'object': obj
#         })

