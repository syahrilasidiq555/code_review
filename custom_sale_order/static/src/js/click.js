        odoo.define('custom_crm.view_crm_cost_sheet', function (require){
        "use strict";
        var form_widget = require('web.form_widgets');
        var core = require('web.core');
        var _t = core._t;
        var QWeb = core.qweb;

            form_widget.WidgetButton.include({
                on_click: function() {
                    if(this.node.attrs.custom === "click"){
                        var xls_url = $("#xls_url_div").text();
                        print(xls_url);
                        $("#xls_export").attr("href", xls_url);
                        var a = document.createElement('a');
                        a.href = 'alert::';
                        a.target = '_self';
                        a.click();
                        return;
                    }
                    this._super();
                },
            });
        });