/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class DeprecLinesToggler extends Component {
    setup() {
        this.orm = useService("orm");
    }

    get isPosted() {
        return this.props.record.data.move_posted_check;
    }

    get isWaiting() {
        return this.props.record.data.move_check;
    }

    get disabled() {
        return this.isPosted || this.isWaiting;
    }

    get buttonClass() {
        if (this.isPosted) {
            return "o_is_posted";
        }
        if (this.isWaiting) {
            return "o_unposted";
        }
        return "";
    }

    get title() {
        if (this.isPosted) {
            return "Posted";
        }
        if (this.isWaiting) {
            return "Accounting entries waiting for manual verification";
        }
        return "Unposted";
    }

    async onClick(ev) {
        ev.stopPropagation();

        if (this.disabled) {
            return;
        }

        await this.orm.call(
            "account.asset.depreciation.line",
            "create_move",
            [[this.props.record.resId]]
        );

        await this.props.record.model.load();
    }
}

DeprecLinesToggler.template = "account_asset_toggle.DeprecLinesToggler";

registry.category("fields").add(
    "deprec_lines_toggler",
    DeprecLinesToggler
);
