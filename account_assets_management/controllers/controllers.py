# -*- coding: utf-8 -*-
# from odoo import http


# class AccountAssetsManagement(http.Controller):
#     @http.route('/account_assets_management/account_assets_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_assets_management/account_assets_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_assets_management.listing', {
#             'root': '/account_assets_management/account_assets_management',
#             'objects': http.request.env['account_assets_management.account_assets_management'].search([]),
#         })

#     @http.route('/account_assets_management/account_assets_management/objects/<model("account_assets_management.account_assets_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_assets_management.object', {
#             'object': obj
#         })

