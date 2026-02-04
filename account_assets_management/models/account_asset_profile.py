# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountAssetProfile(models.Model):
    _name = "account.asset.profile"
    _inherit = ["analytic.mixin"]
    _description = "Asset Profile"
    _order = "name"
    _check_company_auto = True

    # =====================================================
    # BASIC INFORMATION
    # =====================================================

    name = fields.Char(
        string="Asset Profile Name",
        required=True,
        index=True,
        help=(
            "Nama template profil aset (contoh: 'Elektronik', 'Kendaraan'). "
            "Digunakan untuk pengisian otomatis saat membuat aset baru."
        )
    )

    code = fields.Char(
        string="Asset Profile Code",
        required=True,
        index=True,
        help="Kode unik profil aset untuk memudahkan pencarian (contoh: AP-ELEC, AP-VEH)."
    )

    color = fields.Integer(string='Color Index')

    note = fields.Text(
        string="Notes",
        help="Catatan internal mengenai kebijakan akuntansi untuk profil aset ini."
    )

    active = fields.Boolean(
        default=True,
        help="Jika dimatikan (archived), profil ini tidak tersedia untuk dipilih."
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help="Perusahaan pemilik profil aset ini (multi-company aware)."
    )

    type = fields.Selection(
        [
            ('purchase', 'Purchase / Asset'),
            ('sale', 'Sale / Revenue Recognition'),
        ],
        string="Profile Type",
        required=True,
        default='purchase',
        help=(
            "Purchase: Untuk aset tetap (beban depresiasi).\n"
            "Sale: Untuk pendapatan diterima dimuka (amortisasi pendapatan)."
        )
    )

    # =====================================================
    # ASSET CLASSIFICATION
    # =====================================================

    asset_kind = fields.Selection(
        [
            ('tangible', 'Tangible Asset (Berwujud)'),
            ('intangible', 'Intangible Asset (Tak Berwujud)'),
            ('biological', 'Biological Asset'),
        ],
        string='Asset Kind',
        default='tangible',
        required=True,
        help=(
            "Klasifikasi aset berdasarkan sifat fisiknya. "
            "Digunakan untuk membedakan perlakuan depresiasi, amortisasi, "
            "atau penilaian aset biologis."
        )
    )

    is_depreciable = fields.Boolean(default=True)

    open_asset = fields.Boolean(
        string='Skip Draft State',
        help="Jika aktif, aset langsung berstatus Running tanpa konfirmasi manual."
    )

    # =====================================================
    # ACCOUNT CONFIGURATION
    # =====================================================

    account_asset_id = fields.Many2one(
        'account.account',
        string='Asset Account',
        required=True,
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        help="Akun neraca yang mencatat nilai perolehan aset."
    )

    account_depreciation_id = fields.Many2one(
        'account.account',
        string='Accumulated Depreciation Account',
        required=True,
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        help="Akun kontra-aset untuk mencatat akumulasi penyusutan."
    )

    account_depreciation_expense_id = fields.Many2one(
        'account.account',
        string='Depreciation Expense Account',
        required=True,
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        help="Akun laba rugi untuk mencatat beban depresiasi atau amortisasi."
    )

    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
        check_company=True,
        help="Jurnal akuntansi untuk pencatatan otomatis depresiasi."
    )

    # analytic_distribution diwarisi dari analytic.mixin (Odoo 17)
    # Digunakan untuk pembagian biaya ke beberapa analytic plan

    # =====================================================
    # DEPRECIATION / AMORTIZATION CONFIG
    # =====================================================

    method = fields.Selection(
        [('linear', 'Linear'),
         ('degressive', 'Degressive'),
         ('double_declining', 'Double Declining'),
         ('custom', 'Custom Formula')],
        string='Computation Method',
        required=True,
        default='linear',
        help=(
            "Linear: Beban tetap setiap periode.\n"
            "Degressive: Beban menurun berdasarkan faktor pengali."
        )
    )

    custom_formula = fields.Char(
        string="Custom Formula",
        help="Variables: book_value, remaining_amount, period_factor"
    )

    method_time = fields.Selection(
        [
            ('number', 'Number of Entries'),
            ('end', 'Ending Date'),
        ],
        string='Time Method',
        required=True,
        default='number',
        help=(
            "Number: Berdasarkan jumlah jurnal depresiasi.\n"
            "Ending Date: Berdasarkan tanggal akhir masa manfaat."
        )
    )

    method_number = fields.Integer(
        string='Number of Depreciations',
        default=5,
        help="Jumlah total jurnal depresiasi yang akan dibuat."
    )

    method_period = fields.Integer(
        string='Period Length (Months)',
        default=1,
        required=True,
        help="Interval waktu antar depresiasi dalam satuan bulan."
    )

    method_end = fields.Date(
        string='Ending Date',
        help="Tanggal akhir depresiasi jika menggunakan metode Ending Date."
    )

    method_progress_factor = fields.Float(
        string='Degressive Factor',
        default=0.3,
        help="Faktor saldo menurun untuk metode degressive (nilai antara 0 dan 1)."
    )

    prorata = fields.Boolean(
        string='Prorata Temporis',
        help="Hitung depresiasi periode pertama secara proporsional berdasarkan tanggal mulai."
    )

    group_entries = fields.Boolean(
        string="Group Journal Entries",
        default=False,
        help="Jika dicentang, penyusutan untuk semua aset dalam kategori ini akan digabung menjadi satu jurnal per bulan."
    )

    _sql_constraints = [
        (
            'asset_profile_code_company_uniq',
            'unique(code, company_id)',
            'Asset Profile Code harus unik per Company.'
        ),
    ]

    # =====================================================
    # CONSTRAINTS & ONCHANGE
    # =====================================================

    @api.constrains(
        'method',
        'method_progress_factor',
        'method_time',
        'method_number',
        'method_period',
        'method_end'
    )
    def _check_values(self):
        """Validasi konfigurasi untuk mencegah error perhitungan depresiasi."""
        for rec in self:
            if rec.method == 'degressive' and not (0 < rec.method_progress_factor < 1):
                raise ValidationError(
                    _("Degressive factor harus di antara 0 dan 1."))

            if rec.method == 'custom' and not rec.custom_formula:
                raise ValidationError(_("Custom Formula wajib diisi."))
            if rec.method_time == 'number' and rec.method_number <= 0:
                raise ValidationError(_("Jumlah depresiasi harus minimal 1."))

            if rec.method_period <= 0:
                raise ValidationError(
                    _("Panjang periode harus minimal 1 bulan."))

            if rec.method_time == 'end' and not rec.method_end:
                raise ValidationError(
                    _("Ending Date wajib diisi jika Time Method = Ending Date."))

    @api.onchange('method')
    def _onchange_method(self):
        if self.method != 'custom':
            self.custom_formula = False


    @api.onchange('account_asset_id', 'type')
    def _onchange_account_asset_id(self):
        """
        Sugesti otomatis akun terkait agar meminimalkan kesalahan input user.
        """
        if not self.account_asset_id:
            return

        if self.type == 'purchase' and not self.account_depreciation_id:
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': _('Silakan pilih akun akumulasi depresiasi secara manual.')
                }
            }

        if self.type == 'sale' and not self.account_depreciation_expense_id:
            self.account_depreciation_expense_id = self.account_asset_id

    # =====================================================
    # ORM OVERRIDE
    # =====================================================

    @api.model_create_multi
    def create(self, vals_list):
        profiles = super().create(vals_list)

        for profile in profiles:
            if (
                profile.account_asset_id
                and 'asset_profile_id' in profile.account_asset_id._fields
            ):
                profile.account_asset_id.asset_profile_id = profile.id
                _logger.info(
                    "Asset Profile '%s' linked to Account '%s' (%s)",
                    profile.name,
                    profile.account_asset_id.display_name,
                    profile.company_id.name
                )

        return profiles

    def write(self, vals):
        # Simpan akun lama sebelum update untuk pembersihan
        old_accounts = {rec.id: rec.account_asset_id for rec in self}
        res = super(AccountAssetProfile, self).write(vals)

        if 'account_asset_id' in vals:
            for rec in self:
                # 1. Lepas link dari akun lama
                old_acc = old_accounts.get(rec.id)
                if old_acc and old_acc.id != rec.account_asset_id.id:
                    old_acc.asset_profile_id = False

                # 2. Pasang link ke akun baru
                if rec.account_asset_id:
                    rec.account_asset_id.asset_profile_id = rec.id
        return res

    def unlink(self):
        # Bersihkan referensi di account.account sebelum dihapus
        for rec in self:
            if rec.account_asset_id:
                rec.account_asset_id.asset_profile_id = False
        return super(AccountAssetProfile, self).unlink()

    @api.onchange('method_time')
    def _onchange_method_time(self):
        """ Reset nilai jika user mengganti metode waktu """
        if self.method_time == 'number':
            self.method_end = False
        else:
            self.method_number = 0
