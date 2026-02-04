# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AccountAssetCompute(models.TransientModel):
    _name = 'account.asset.compute'
    _description = "Compute Assets Depreciation"

    date_end = fields.Date(
        string='Depreciate Until', 
        required=True, 
        default=fields.Date.context_today,
        help="Semua baris depresiasi sampai tanggal ini akan diposting."
    )
    note = fields.Text(string='Processing Result', readonly=True)
    move_ids = fields.Many2many(
        'account.move', 
        string='Created Entries', 
        readonly=True
    )

    def asset_compute(self):
        self.ensure_one()
        
        # 1. Cari aset yang aktif
        assets = self.env['account.asset'].search([('state', '=', 'open')])
        if not assets:
            raise UserError(_("Tidak ada aset dengan status 'Running' untuk diproses."))

        # 2. Catat ID Journal Entry yang sudah ada untuk filter nanti
        old_move_ids = self.env['account.move'].search([
            ('asset_id', 'in', assets.ids)
        ]).ids

        # 3. Eksekusi posting dari model utama account.asset
        assets.action_post_depreciation(date=self.date_end)

        # 4. Cari Journal Entry baru yang terbentuk khusus untuk aset-aset tersebut
        new_moves = self.env['account.move'].search([
            ('asset_id', 'in', assets.ids),
            ('id', 'not in', old_move_ids),
            ('date', '<=', self.date_end)
        ])

        # 5. Update status wizard
        msg = _("Berhasil memproses %s baris penyusutan hingga tanggal %s.") % (len(new_moves), self.date_end)
        self.write({
            'note': msg,
            'move_ids': [(6, 0, new_moves.ids)]
        })

        # 6. Tampilkan kembali wizard dengan view hasil (result)
        # Pastikan ID view eksternal ini benar di XML Anda
        try:
            view_id = self.env.ref('account_asset_compute.account_asset_compute_view_form_result').id
        except ValueError:
            view_id = False # Fallback ke default view jika ref tidak ditemukan

        return {
            'name': _('Depreciation Result'),
            'view_mode': 'form',
            'res_model': 'account.asset.compute',
            'res_id': self.id,
            'view_id': view_id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def view_asset_moves(self):
        """ Fungsi untuk melihat daftar journal entry yang baru dibuat """
        self.ensure_one()
        return {
            'name': _('Created Journal Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.move_ids.ids)],
            'target': 'current',
        }