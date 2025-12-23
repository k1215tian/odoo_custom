# -*- coding: utf-8 -*-
# from odoo import http


# class HrJob(http.Controller):
#     @http.route('/hr_job/hr_job', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_job/hr_job/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_job.listing', {
#             'root': '/hr_job/hr_job',
#             'objects': http.request.env['hr_job.hr_job'].search([]),
#         })

#     @http.route('/hr_job/hr_job/objects/<model("hr_job.hr_job"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_job.object', {
#             'object': obj
#         })

