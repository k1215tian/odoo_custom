# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class AssetModify(models.TransientModel):
    _name = 'asset.modify'
    _description = 'Modify Asset'

    name = fields.Text(string='Reason', required=True, help="Alasan perubahan masa manfaat.")
    method_number = fields.Integer(string='Number of Depreciations', required=True)
    method_period = fields.Integer(string='Period Length (Months)', required=True)
    date_start = fields.Date(string='Start Date') # Menyesuaikan field di account_asset.py Anda

    @api.model
    def default_get(self, fields_list):
        res = super(AssetModify, self).default_get(fields_list)
        asset_id = self.env.context.get('active_id')
        if asset_id:
            asset = self.env['account.asset'].browse(asset_id)
            if 'name' in fields_list:
                res.update({'name': asset.name})
            if 'method_number' in fields_list:
                res.update({'method_number': asset.method_number})
            if 'method_period' in fields_list:
                res.update({'method_period': asset.method_period})
            if 'date_start' in fields_list:
                res.update({'date_start': asset.date_start})
        return res

    # def modify(self):
    #     """ Memodifikasi durasi aset dan menghitung ulang jadwal penyusutan. """
    #     self.ensure_one()
    #     asset_id = self.env.context.get('active_id')
    #     if not asset_id:
    #         return {'type': 'ir.actions.act_window_close'}

    #     asset = self.env['account.asset'].browse(asset_id)
        
    #     # Cek apakah sudah ada jurnal yang diposting
    #     posted_lines = asset.depreciation_line_ids.filtered(lambda l: l.move_id)
    #     if posted_lines:
    #         raise UserError(_("Aset tidak dapat dimodifikasi karena sudah ada penyusutan yang terposting jurnal. Silakan batalkan jurnal terkait terlebih dahulu."))

    #     # Simpan nilai lama untuk keperluan tracking/chatter
    #     old_values = {
    #         'method_number': asset.method_number,
    #         'method_period': asset.method_period,
    #     }

    #     # Update nilai baru ke model aset
    #     asset.write({
    #         'method_number': self.method_number,
    #         'method_period': self.method_period,
    #     })

    #     # Hitung ulang jadwal (menggunakan fungsi yang sudah ada di account_asset.py Anda)
    #     asset.compute_depreciation_board()

    #     # Log perubahan ke Chatter
    #     msg = _("<b>Depreciation Board Modified</b><br/>Reason: %s") % self.name
    #     asset.message_post(body=msg)
        
    #     return {'type': 'ir.actions.act_window_close'}

    def modify(self):
        self.ensure_one()
        asset_id = self.env.context.get('active_id')
        if not asset_id:
            return {'type': 'ir.actions.act_window_close'}
        asset = self.env['account.asset'].browse(asset_id)
        
        # [FIX] Logic: Jangan block jika sudah ada posted lines.
        # Tapi pastikan method_number baru > jumlah periode yang sudah lewat.
        posted_count = len(asset.depreciation_line_ids.filtered(lambda l: l.move_id))
        
        if self.method_number <= posted_count:
            raise UserError(_("Durasi baru tidak boleh lebih kecil dari jumlah periode yang sudah diposting (%s).") % posted_count)

        # Update Asset
        asset.write({
            'method_number': self.method_number,
            'method_period': self.method_period,
        })
        
        # Trigger re-calculation (Fungsi compute_depreciation_board di account_asset.py sudah kita perbaiki 
        # untuk menghapus line draft dan melanjutkan hitungan sisa).
        asset.compute_depreciation_board()
        
        asset.message_post(body=_("Asset duration modified. Reason: %s") % self.name)
        return {'type': 'ir.actions.act_window_close'}