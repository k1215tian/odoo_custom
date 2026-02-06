# -*- coding: utf-8 -*-
# from odoo import http


# class HrTerminationAssets(http.Controller):
#     @http.route('/hr_termination_assets/hr_termination_assets', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_termination_assets/hr_termination_assets/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_termination_assets.listing', {
#             'root': '/hr_termination_assets/hr_termination_assets',
#             'objects': http.request.env['hr_termination_assets.hr_termination_assets'].search([]),
#         })

#     @http.route('/hr_termination_assets/hr_termination_assets/objects/<model("hr_termination_assets.hr_termination_assets"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_termination_assets.object', {
#             'object': obj
#         })

