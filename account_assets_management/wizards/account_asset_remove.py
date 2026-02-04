# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AccountAssetRemove(models.TransientModel):
    _name = 'account.asset.remove'
    _description = "Remove Asset Wizard"

    removal_type = fields.Selection([
        ('scrap', 'Scrapping (Write-off)'),
        ('destroy', 'Destroyed (Dihancurkan/Musnah)'),
        ('sale', 'Sale (Dijual)')
    ], string="Removal Type", default='scrap', required=True,
       help="Pilih metode penghapusan aset.\n"
            "- Scrapping: Aset dibuang karena rusak/tua.\n"
            "- Destroyed: Aset hancur (bencana/kecelakaan).\n"
            "- Sale: Aset dijual ke pihak lain.")
    
    date_remove = fields.Date(
        string="Removal Date", 
        required=True, 
        default=fields.Date.today,
        help="Tanggal aset dihapus/dijual. Jurnal akan terbentuk pada tanggal ini."
    )
    
    sale_value = fields.Monetary(string="Sale Price", help="Harga jual aset (jika tipe Sale).")
    currency_id = fields.Many2one(
        'res.currency', 
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )
    
    account_sale_id = fields.Many2one(
        'account.account', 
        string="Difference/Loss Account", 
        required=True,
        domain="[('deprecated', '=', False)]",
        help="Akun untuk menampung selisih nilai buku (Rugi Pelepasan Aset)."
    )
    account_loss_id = fields.Many2one('account.account', string="Loss Account (Scrap)")
    account_receivable_id = fields.Many2one(
        'account.account',
        string="Receivable/Bank Account (For Sale)",
        domain="[('deprecated', '=', False)]",
        help="Hanya diisi jika tipe 'Sale'. Akun untuk mencatat penerimaan uang (Debit)."
    )
    note = fields.Text("Reason/Notes")

    def action_remove_asset(self):
        self.ensure_one()
        asset_id = self._context.get('active_id')
        asset = self.env['account.asset'].browse(asset_id)
        
        # 1. PROTEKSI STATUS & VALIDASI
        # Mencegah eksekusi ulang pada aset yang sudah dihapus atau masih draft
        if not asset or asset.state == 'removed':
            raise UserError(_("Aset ini sudah dihapus atau tidak ditemukan."))
        if asset.state != 'open':
            raise UserError(_("Hanya aset dengan status 'Running' yang dapat diproses disposal."))
        if self.date_remove < asset.date_start:
            raise UserError(_("Tanggal penghapusan tidak boleh sebelum tanggal mulai aset."))

        # 2. UPDATE NILAI BUKU TERAKHIR
        # Posting depresiasi yang menggantung hingga tanggal disposal agar saldo akurat
        if hasattr(asset, 'action_post_depreciation'):
            asset.action_post_depreciation(date=self.date_remove)

        profile = asset.profile_id
        purchase_value = asset.purchase_value
        
        # Hitung akumulasi hanya dari baris yang sudah terposting ke jurnal
        posted_lines = asset.depreciation_line_ids.filtered(lambda l: l.move_id and l.type == 'depreciate')
        accumulated_depr = sum(posted_lines.mapped('amount'))
        
        # Sisa nilai buku yang akan dipaksa menjadi 0 (diakui sebagai kerugian)
        book_value_to_clear = purchase_value - accumulated_depr
        proceeds = self.sale_value if self.removal_type == 'sale' else 0.0

        # 3. KONSTRUKSI JURNAL DISPOSAL (FORCE ZERO)
        move_lines = []
        ref_label = dict(self._fields['removal_type'].selection).get(self.removal_type)

        # A. KREDIT: Akun Aset (Full Original Value) -> Saldo Aset di Neraca jadi 0
        move_lines.append((0, 0, {
            'name': f"Disposal Clearance: {asset.name}",
            'account_id': profile.account_asset_id.id,
            'debit': 0.0,
            'credit': purchase_value,
            'analytic_distribution': asset.analytic_distribution,
        }))

        # B. DEBIT: Akun Akumulasi (Total Posted) -> Saldo Akumulasi di Neraca jadi 0
        if not asset.currency_id.is_zero(accumulated_depr):
            move_lines.append((0, 0, {
                'name': f"Accum. Depr Clearance: {asset.name}",
                'account_id': profile.account_depreciation_id.id,
                'debit': accumulated_depr,
                'credit': 0.0,
            }))

        # C. DEBIT: Kas/Piutang (Jika dijual)
        if self.removal_type == 'sale' and not asset.currency_id.is_zero(proceeds):
            if not self.account_receivable_id:
                raise UserError(_("Harap isi Akun Piutang/Kas untuk tipe penjualan."))
            move_lines.append((0, 0, {
                'name': f"Proceeds from {asset.name}",
                'account_id': self.account_receivable_id.id,
                'debit': proceeds,
                'credit': 0.0,
            }))

        # D. BALANCING: Selisih Laba/Rugi
        # Net Balance = (Proceeds + Accum) - Purchase Value
        net_gain_loss = proceeds + accumulated_depr - purchase_value
        
        if not asset.currency_id.is_zero(net_gain_loss):
            move_lines.append((0, 0, {
                'name': _("Gain/Loss on Asset Disposal: %s") % asset.name,
                'account_id': self.account_sale_id.id,
                'debit': abs(net_gain_loss) if net_gain_loss < 0 else 0.0,
                'credit': net_gain_loss if net_gain_loss > 0 else 0.0,
                'analytic_distribution': asset.analytic_distribution,
            }))

        # 4. PEMBUATAN & POSTING JURNAL
        move = self.env['account.move'].create({
            'ref': f"DISPOSAL/{asset.name}",
            'date': self.date_remove,
            'journal_id': profile.journal_id.id,
            'move_type': 'entry',
            'line_ids': move_lines
        })
        move.action_post()

        # 5. LOCKDOWN & CLEANUP (Memaksa nilai 0 di sistem)
        # Hapus semua jadwal depresiasi masa depan agar tidak bisa di-post secara tidak sengaja
        asset.depreciation_line_ids.filtered(lambda l: not l.move_id).unlink()

        # Catat baris removal sebagai penutup history aset
        self.env['account.asset.line'].create({
            'asset_id': asset.id,
            'name': _("Final Disposal (%s) - Forced to Zero") % ref_label,
            'amount': book_value_to_clear,
            'line_date': self.date_remove,
            'type': 'remove',
            'move_id': move.id
        })

        # Tandai aset sebagai dihapus dan arsipkan (active=False)
        asset.write({
            'state': 'removed', 
            'active': False,
            'message_main_attachment_id': False # Opsional: bersih-bersih attachment
        })

        return {'type': 'ir.actions.act_window_close'}