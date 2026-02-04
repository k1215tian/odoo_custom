# -*- coding: utf-8 -*-
import logging
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountAssetLine(models.Model):
    _name = "account.asset.line"
    _description = "Asset Depreciation Line"
    _order = "line_date asc, id asc"

    name = fields.Char(string='Depreciation Name', required=True, readonly=True,
                       help="Nama baris depresiasi, contoh: 'Laptop - Depresiasi 1/12'.")
    asset_id = fields.Many2one('account.asset', string='Asset', required=True, ondelete='cascade', index=True,
                               help="Aset induk yang terkait dengan baris penyusutan ini.")
    type = fields.Selection([('depreciation', 'Depreciation'), ('create', 'Acquisition'), ('remove', 'Removal')],
                            default='depreciation', string='Line Type',
                            help="Jenis transaksi: Depreciation, Acquisition, Removal.")
    amount = fields.Monetary(string='Depreciation Amount', currency_field='currency_id',
                             help="Jumlah penyusutan periode ini.")
    depreciated_value = fields.Monetary(string='Cumulative Depreciation', currency_field='currency_id',
                                        help="Akumulasi penyusutan sampai periode ini.")
    remaining_value = fields.Monetary(string='Residual Value', currency_field='currency_id',
                                      help="Nilai buku setelah dikurangi akumulasi penyusutan.")
    line_date = fields.Date(string='Depreciation Date', required=True, index=True,
                            help="Tanggal pengakuan beban penyusutan di jurnal.")
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True, copy=False,
                              help="Referensi jurnal entry yang dibuat dari baris ini.")
    currency_id = fields.Many2one('res.currency', related='asset_id.currency_id', store=True, readonly=True,
                                  help="Mata uang perhitungan mengikuti aset.")

    # -------------------------------
    # METHODS
    # -------------------------------
    def unlink(self):
        """ Mencegah penghapusan jika baris sudah memiliki Journal Entry. """
        for line in self:
            if line.move_id:
                raise UserError(
                    _("Baris '%s' tidak bisa dihapus karena sudah terposting ke jurnal.") % line.name)
        return super().unlink()

    def create_move(self):
        """ 
        Membuat Journal Entry individual dengan efisiensi database yang ditingkatkan.
        """
        # Optimasi 1: Gunakan sudo() jika proses depresiasi otomatis dilakukan oleh sistem/cron
        # Optimasi 2: Pastikan context allow_asset terbawa hingga proses posting
        for line in self:
            if line.move_id or line.amount <= 0:
                continue

            asset = line.asset_id
            profile = asset.profile_id

            if not (profile.account_depreciation_id and profile.account_depreciation_expense_id):
                raise UserError(
                    _("Akun depresiasi pada profil %s belum diset.") % profile.name)

            # Siapkan vals
            move_vals = line._prepare_move_vals()

            # Optimasi 3: Membungkus seluruh operasi dalam context manager yang sama
            # agar method override di account.move (seperti constrains) tidak mencekal.
            move = self.sudo().env['account.move'].with_context(
                allow_asset=True).create(move_vals)
            move.action_post()

            line.write({'move_id': move.id})
        return True

    def create_grouped_move(self):
        """Membuat Journal Entry gabungan berdasarkan Profile dan Tanggal."""
        if not self:
            return True

        # Kelompokkan baris berdasarkan Profile dan Tanggal
        grouped_data = {}
        for line in self:
            if line.move_id or line.currency_id.is_zero(line.amount):
                continue

            # Key pengelompokan: (ID Profil, Tanggal Depresiasi)
            key = (line.asset_id.profile_id.id, line.line_date)
            grouped_data.setdefault(key, self.env['account.asset.line'])
            grouped_data[key] |= line

        for (profile_id, line_date), lines in grouped_data.items():
            profile = self.env['account.asset.profile'].browse(profile_id)
            total_amount = sum(lines.mapped('amount'))

            move_vals = {
                'date': line_date,
                'journal_id': profile.journal_id.id,
                'ref': _("Grouped Depreciation - %s") % profile.name,
                'move_type': 'entry',
                'line_ids': [
                    (0, 0, {
                        'name': _("Grouped Depreciation: %s") % profile.name,
                        'account_id': profile.account_depreciation_expense_id.id,
                        'debit': total_amount,
                        'credit': 0.0,
                    }),
                    (0, 0, {
                        'name': _("Grouped Depreciation: %s") % profile.name,
                        'account_id': profile.account_depreciation_id.id,
                        'debit': 0.0,
                        'credit': total_amount,
                    }),
                ]
            }

            move = self.env['account.move'].create(move_vals)
            move.action_post()
            lines.write({'move_id': move.id})

        return True

    def _prepare_move_vals(self):
        """ 
        Menyiapkan dictionary untuk pembuatan Journal Entry untuk asset ini.

        Mengembalikan struktur dict yang siap digunakan untuk membuat jurnal,
        termasuk informasi tanggal, jurnal, referensi, dan baris debit/credit. 
        """
        self.ensure_one()
        asset = self.asset_id
        profile = asset.profile_id

        return {
            'date': self.line_date,
            'journal_id': profile.journal_id.id,
            'ref': f"{asset.code or asset.name} - {self.name}",
            'move_type': 'entry',
            'asset_id': asset.id,  # Link balik untuk audit trail; juga bisa dipakai modul lain
            'line_ids': [
                (0, 0, {
                    'name': self.name,
                    'account_id': profile.account_depreciation_expense_id.id,
                    'debit': self.amount,
                    'credit': 0.0,
                    'analytic_distribution': asset.analytic_distribution,
                }),
                (0, 0, {
                    'name': self.name,
                    'account_id': profile.account_depreciation_id.id,
                    'debit': 0.0,
                    'credit': self.amount,
                    'analytic_distribution': asset.analytic_distribution,
                }),
            ]
        }
