odoo.define('custom_dashboard.dashboard_action', function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var _t = core._t;
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var ajax = require('web.ajax');
    var web_client = require('web.web_client');
    var AnalisaKeuanganDashboard = AbstractAction.extend({
        template: 'AnalisaKeuanganDashboard',
        events: {
            'click .rasio_hutang': function(e) {
                let value = $('#income_expense_values').val();
                let period
                if (value=="this_year"){
                    period = 'year'
                }else if (value=="this_month"){
                    period = 'month'
                }else if (value=="this_week"){
                    period = 'week'
                }else if (value=="this_day"){
                    period = 'day'
                }
                // console.log(period)
    
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                var options = {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                };
                this._rpc({
                    model: 'analisa.keuangan',
                    method: 'get_rasio_hutang',
                    args: [period,true],
                }).then(function (result) {
                    self.do_action({
                        name: result['name'],
                        type: result['type'],
                        res_model: result['res_model'],
                        view_mode: result['view_mode'],
                        views: result['views'],
                        domain: result['domain'],
                        context: result['context'],
                        target: result['target'],
                    }, options)
                })
            },
            'click .rasio_hutang_pendekatan_modal': function(e) {
                let value = $('#income_expense_values').val();
                let period
                if (value=="this_year"){
                    period = 'year'
                }else if (value=="this_month"){
                    period = 'month'
                }else if (value=="this_week"){
                    period = 'week'
                }else if (value=="this_day"){
                    period = 'day'
                }
                // console.log(period)
    
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                var options = {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                };
                this._rpc({
                    model: 'analisa.keuangan',
                    method: 'get_rasio_hutang_pendekatan_modal',
                    args: [period,true],
                }).then(function (result) {
                    self.do_action({
                        name: result['name'],
                        type: result['type'],
                        res_model: result['res_model'],
                        view_mode: result['view_mode'],
                        views: result['views'],
                        domain: result['domain'],
                        context: result['context'],
                        target: result['target'],
                    }, options)
                })
            },
            'click .rasio_lancar': function(e) {
                let value = $('#income_expense_values').val();
                let period
                if (value=="this_year"){
                    period = 'year'
                }else if (value=="this_month"){
                    period = 'month'
                }else if (value=="this_week"){
                    period = 'week'
                }else if (value=="this_day"){
                    period = 'day'
                }
                // console.log(period)
    
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                var options = {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                };
                this._rpc({
                    model: 'analisa.keuangan',
                    method: 'get_rasio_lancar',
                    args: [period,true],
                }).then(function (result) {
                    self.do_action({
                        name: result['name'],
                        type: result['type'],
                        res_model: result['res_model'],
                        view_mode: result['view_mode'],
                        views: result['views'],
                        domain: result['domain'],
                        context: result['context'],
                        target: result['target'],
                    }, options)
                })
            },
            'click .rasio_kas': function(e) {
                let value = $('#income_expense_values').val();
                let period
                if (value=="this_year"){
                    period = 'year'
                }else if (value=="this_month"){
                    period = 'month'
                }else if (value=="this_week"){
                    period = 'week'
                }else if (value=="this_day"){
                    period = 'day'
                }
                // console.log(period)
    
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                var options = {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                };
                this._rpc({
                    model: 'analisa.keuangan',
                    method: 'get_rasio_kas',
                    args: [period,true],
                }).then(function (result) {
                    self.do_action({
                        name: result['name'],
                        type: result['type'],
                        res_model: result['res_model'],
                        view_mode: result['view_mode'],
                        views: result['views'],
                        domain: result['domain'],
                        context: result['context'],
                        target: result['target'],
                    }, options)
                })
            },
            'click .rasio_cepat': function(e) {
                let value = $('#income_expense_values').val();
                let period
                if (value=="this_year"){
                    period = 'year'
                }else if (value=="this_month"){
                    period = 'month'
                }else if (value=="this_week"){
                    period = 'week'
                }else if (value=="this_day"){
                    period = 'day'
                }
                // console.log(period)
    
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                var options = {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                };
                this._rpc({
                    model: 'analisa.keuangan',
                    method: 'get_rasio_cepat',
                    args: [period,true],
                }).then(function (result) {
                    self.do_action({
                        name: result['name'],
                        type: result['type'],
                        res_model: result['res_model'],
                        view_mode: result['view_mode'],
                        views: result['views'],
                        domain: result['domain'],
                        context: result['context'],
                        target: result['target'],
                    }, options)
                })
            },
            'click .rasio_perputaran_persediaan': function(e) {
                let value = $('#income_expense_values').val();
                let period
                if (value=="this_year"){
                    period = 'year'
                }else if (value=="this_month"){
                    period = 'month'
                }else if (value=="this_week"){
                    period = 'week'
                }else if (value=="this_day"){
                    period = 'day'
                }
                // console.log(period)
    
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                var options = {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                };
                this._rpc({
                    model: 'analisa.keuangan',
                    method: 'get_rasio_perputaran_persediaan',
                    args: [period,true],
                }).then(function (result) {
                    self.do_action({
                        name: result['name'],
                        type: result['type'],
                        res_model: result['res_model'],
                        view_mode: result['view_mode'],
                        views: result['views'],
                        domain: result['domain'],
                        context: result['context'],
                        target: result['target'],
                    }, options)
                })
            },
            'click .rasio_perputaran_piutang': function(e) {
                let value = $('#income_expense_values').val();
                let period
                if (value=="this_year"){
                    period = 'year'
                }else if (value=="this_month"){
                    period = 'month'
                }else if (value=="this_week"){
                    period = 'week'
                }else if (value=="this_day"){
                    period = 'day'
                }
                // console.log(period)
    
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                var options = {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                };
                this._rpc({
                    model: 'analisa.keuangan',
                    method: 'get_rasio_perputaran_piutang',
                    args: [period,true],
                }).then(function (result) {
                    self.do_action({
                        name: result['name'],
                        type: result['type'],
                        res_model: result['res_model'],
                        view_mode: result['view_mode'],
                        views: result['views'],
                        domain: result['domain'],
                        context: result['context'],
                        target: result['target'],
                    }, options)
                })
            },
            'click .rasio_perputaran_aktiva_tetap': function(e) {
                let value = $('#income_expense_values').val();
                let period
                if (value=="this_year"){
                    period = 'year'
                }else if (value=="this_month"){
                    period = 'month'
                }else if (value=="this_week"){
                    period = 'week'
                }else if (value=="this_day"){
                    period = 'day'
                }
                // console.log(period)
    
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                var options = {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                };
                this._rpc({
                    model: 'analisa.keuangan',
                    method: 'get_rasio_perputaran_aktiva_tetap',
                    args: [period,true],
                }).then(function (result) {
                    self.do_action({
                        name: result['name'],
                        type: result['type'],
                        res_model: result['res_model'],
                        view_mode: result['view_mode'],
                        views: result['views'],
                        domain: result['domain'],
                        context: result['context'],
                        target: result['target'],
                    }, options)
                })
            },
            'click .rasio_perputaran_total_aktiva': function(e) {
                let value = $('#income_expense_values').val();
                let period
                if (value=="this_year"){
                    period = 'year'
                }else if (value=="this_month"){
                    period = 'month'
                }else if (value=="this_week"){
                    period = 'week'
                }else if (value=="this_day"){
                    period = 'day'
                }
                // console.log(period)
    
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                var options = {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                };
                this._rpc({
                    model: 'analisa.keuangan',
                    method: 'get_rasio_perputaran_total_aktiva',
                    args: [period,true],
                }).then(function (result) {
                    self.do_action({
                        name: result['name'],
                        type: result['type'],
                        res_model: result['res_model'],
                        view_mode: result['view_mode'],
                        views: result['views'],
                        domain: result['domain'],
                        context: result['context'],
                        target: result['target'],
                    }, options)
                })
            },
            'click .rasio_margin_laba_kotor': function(e) {
                let value = $('#income_expense_values').val();
                let period
                if (value=="this_year"){
                    period = 'year'
                }else if (value=="this_month"){
                    period = 'month'
                }else if (value=="this_week"){
                    period = 'week'
                }else if (value=="this_day"){
                    period = 'day'
                }
                // console.log(period)
    
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                var options = {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                };
                this._rpc({
                    model: 'analisa.keuangan',
                    method: 'get_rasio_margin_laba_kotor',
                    args: [period,true],
                }).then(function (result) {
                    self.do_action({
                        name: result['name'],
                        type: result['type'],
                        res_model: result['res_model'],
                        view_mode: result['view_mode'],
                        views: result['views'],
                        domain: result['domain'],
                        context: result['context'],
                        target: result['target'],
                    }, options)
                })
            },
            'click .rasio_margin_laba_bersih': function(e) {
                let value = $('#income_expense_values').val();
                let period
                if (value=="this_year"){
                    period = 'year'
                }else if (value=="this_month"){
                    period = 'month'
                }else if (value=="this_week"){
                    period = 'week'
                }else if (value=="this_day"){
                    period = 'day'
                }
                // console.log(period)
    
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                var options = {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                };
                this._rpc({
                    model: 'analisa.keuangan',
                    method: 'get_rasio_margin_laba_bersih',
                    args: [period,true],
                }).then(function (result) {
                    self.do_action({
                        name: result['name'],
                        type: result['type'],
                        res_model: result['res_model'],
                        view_mode: result['view_mode'],
                        views: result['views'],
                        domain: result['domain'],
                        context: result['context'],
                        target: result['target'],
                    }, options)
                })
            },
            'click .rasio_margin_laba_operasi': function(e) {
                let value = $('#income_expense_values').val();
                let period
                if (value=="this_year"){
                    period = 'year'
                }else if (value=="this_month"){
                    period = 'month'
                }else if (value=="this_week"){
                    period = 'week'
                }else if (value=="this_day"){
                    period = 'day'
                }
                // console.log(period)
    
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                var options = {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                };
                this._rpc({
                    model: 'analisa.keuangan',
                    method: 'get_rasio_margin_laba_operasi',
                    args: [period,true],
                }).then(function (result) {
                    self.do_action({
                        name: result['name'],
                        type: result['type'],
                        res_model: result['res_model'],
                        view_mode: result['view_mode'],
                        views: result['views'],
                        domain: result['domain'],
                        context: result['context'],
                        target: result['target'],
                    }, options)
                })
            },
            'click .return_on_investment': function(e) {
                let value = $('#income_expense_values').val();
                let period
                if (value=="this_year"){
                    period = 'year'
                }else if (value=="this_month"){
                    period = 'month'
                }else if (value=="this_week"){
                    period = 'week'
                }else if (value=="this_day"){
                    period = 'day'
                }
                // console.log(period)
    
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                var options = {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                };
                this._rpc({
                    model: 'analisa.keuangan',
                    method: 'get_return_on_investment',
                    args: [period,true],
                }).then(function (result) {
                    self.do_action({
                        name: result['name'],
                        type: result['type'],
                        res_model: result['res_model'],
                        view_mode: result['view_mode'],
                        views: result['views'],
                        domain: result['domain'],
                        context: result['context'],
                        target: result['target'],
                    }, options)
                })
            },
            'click .return_on_assets': function(e) {
                let value = $('#income_expense_values').val();
                let period
                if (value=="this_year"){
                    period = 'year'
                }else if (value=="this_month"){
                    period = 'month'
                }else if (value=="this_week"){
                    period = 'week'
                }else if (value=="this_day"){
                    period = 'day'
                }
                // console.log(period)
    
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                var options = {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                };
                this._rpc({
                    model: 'analisa.keuangan',
                    method: 'get_return_on_assets',
                    args: [period,true],
                }).then(function (result) {
                    self.do_action({
                        name: result['name'],
                        type: result['type'],
                        res_model: result['res_model'],
                        view_mode: result['view_mode'],
                        views: result['views'],
                        domain: result['domain'],
                        context: result['context'],
                        target: result['target'],
                    }, options)
                })
            },

            'change #income_expense_values': function(e) {
                e.stopPropagation();
                var $target = $(e.target);
                var value = $target.val();
                if (value=="this_year"){
                    this.onclick_this_year($target.val());
                }else if (value=="this_month"){
                    this.onclick_this_month($target.val());
                }else if (value=="this_week"){
                    this.onclick_this_week($target.val());
                }else if (value=="this_day"){
                    this.onclick_this_day($target.val());
                }
            },
        },

        init: function (parent, context) {
            this._super(parent, context);
            this.dashboards_templates = ['DashboardRasio'];
            this.today_sale = [];
        },
        willStart: function () {
            var self = this;
            return this._super()
            .then(function () {
                return self.fetch_data();
            });
        },
        start: function () {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function () {
                self.render_dashboards();
                // self.render_graphs();
            });
        },
        // render_graphs: function(){
        //     var self = this;
        //     self.render_pasien_perbulan_graph();
        //     self.onclick_pasien_last_12months();
        // },
        render_dashboards: function () {
            var self = this;
            _.each(this.dashboards_templates, function (template) {
                self.$('.o_pj_dashboard').append(QWeb.render(template, { widget: self }));
            });
        },
        fetch_data: function () {
            var self = this;
            var def1 = this._rpc({
                model: 'analisa.keuangan',
                method: 'get_dashboard_value',
                args: ['day'],
            }).then(function (result) {
                self.company_names = result['company_names']
                self.rasio_hutang = result['rasio_hutang']
                self.rasio_hutang_pendekatan_modal = result['rasio_hutang_pendekatan_modal']
                self.rasio_lancar = result['rasio_lancar']
                self.rasio_kas = result['rasio_kas']
                self.rasio_cepat = result['rasio_cepat']
                self.rasio_perputaran_persediaan = result['rasio_perputaran_persediaan']
                self.rasio_perputaran_piutang = result['rasio_perputaran_piutang']
                self.rasio_perputaran_aktiva_tetap = result['rasio_perputaran_aktiva_tetap']
                self.rasio_perputaran_total_aktiva = result['rasio_perputaran_total_aktiva']
                self.rasio_margin_laba_kotor = result['rasio_margin_laba_kotor']
                self.rasio_margin_laba_bersih = result['rasio_margin_laba_bersih']
                self.rasio_margin_laba_operasi = result['rasio_margin_laba_operasi']
                self.return_on_investment = result['return_on_investment']
                self.return_on_assets = result['return_on_assets']

                // self.total_pasien = result['total_pasien']
                // self.total_pasien_umum = result['total_pasien_umum']
                // self.total_pasien_gigi = result['total_pasien_gigi']
                // self.total_pasien_gizi = result['total_pasien_gizi']
                // self.total_pasien_igd = result['total_pasien_igd']
                // self.total_pasien_kia = result['total_pasien_kia']
                // self.total_pasien_persalinan = result['total_pasien_persalinan']
                // self.top_diagnosa = result['top_diagnosa']
            });
            return $.when(def1);
        },
        

        onclick_this_year: function (ev) {
            var self = this;
            var def1 = this._rpc({
                model: 'analisa.keuangan',
                method: 'get_dashboard_value',
                args: ['year'],
            }).then(function (result) {
                $('#rasio_hutang').empty();
                $('#rasio_hutang').append('<span>' + result['rasio_hutang'] + '</span>');
                $('#rasio_hutang_pendekatan_modal').empty();
                $('#rasio_hutang_pendekatan_modal').append('<span>' + result['rasio_hutang_pendekatan_modal'] + '</span>');
                $('#rasio_lancar').empty();
                $('#rasio_lancar').append('<span>' + result['rasio_lancar'] + '</span>');
                $('#rasio_kas').empty();
                $('#rasio_kas').append('<span>' + result['rasio_kas'] + '</span>');
                $('#rasio_cepat').empty();
                $('#rasio_cepat').append('<span>' + result['rasio_cepat'] + '</span>');
                $('#rasio_perputaran_persediaan').empty();
                $('#rasio_perputaran_persediaan').append('<span>' + result['rasio_perputaran_persediaan'] + '</span>');
                $('#rasio_perputaran_piutang').empty();
                $('#rasio_perputaran_piutang').append('<span>' + result['rasio_perputaran_piutang'] + '</span>');
                $('#rasio_perputaran_aktiva_tetap').empty();
                $('#rasio_perputaran_aktiva_tetap').append('<span>' + result['rasio_perputaran_aktiva_tetap'] + '</span>');
                $('#rasio_perputaran_total_aktiva').empty();
                $('#rasio_perputaran_total_aktiva').append('<span>' + result['rasio_perputaran_total_aktiva'] + '</span>');
                $('#rasio_margin_laba_kotor').empty();
                $('#rasio_margin_laba_kotor').append('<span>' + result['rasio_margin_laba_kotor'] + '</span>');
                $('#rasio_margin_laba_bersih').empty();
                $('#rasio_margin_laba_bersih').append('<span>' + result['rasio_margin_laba_bersih'] + '</span>');
                $('#rasio_margin_laba_operasi').empty();
                $('#rasio_margin_laba_operasi').append('<span>' + result['rasio_margin_laba_operasi'] + '</span>');
                $('#return_on_investment').empty();
                $('#return_on_investment').append('<span>' + result['return_on_investment'] + '</span>');
                $('#return_on_assets').empty();
                $('#return_on_assets').append('<span>' + result['return_on_assets'] + '</span>');

                // $('#top_diagnosa_table_body').empty();
                // result['top_diagnosa'].forEach(d => {
                //     $('#top_diagnosa_table_body').append('<tr><td>'+ d['diagnosa'] +'</td><td>'+ d['count'] +'</td></tr>')
                // });
            });
            return $.when(def1);
        },

        onclick_this_month: function (ev) {
            var self = this;
            var def1 = this._rpc({
                model: 'analisa.keuangan',
                method: 'get_dashboard_value',
                args: ['month'],
            }).then(function (result) {
                $('#rasio_hutang').empty();
                $('#rasio_hutang').append('<span>' + result['rasio_hutang'] + '</span>');
                $('#rasio_hutang_pendekatan_modal').empty();
                $('#rasio_hutang_pendekatan_modal').append('<span>' + result['rasio_hutang_pendekatan_modal'] + '</span>');
                $('#rasio_lancar').empty();
                $('#rasio_lancar').append('<span>' + result['rasio_lancar'] + '</span>');
                $('#rasio_kas').empty();
                $('#rasio_kas').append('<span>' + result['rasio_kas'] + '</span>');
                $('#rasio_cepat').empty();
                $('#rasio_cepat').append('<span>' + result['rasio_cepat'] + '</span>');
                $('#rasio_perputaran_persediaan').empty();
                $('#rasio_perputaran_persediaan').append('<span>' + result['rasio_perputaran_persediaan'] + '</span>');
                $('#rasio_perputaran_piutang').empty();
                $('#rasio_perputaran_piutang').append('<span>' + result['rasio_perputaran_piutang'] + '</span>');
                $('#rasio_perputaran_aktiva_tetap').empty();
                $('#rasio_perputaran_aktiva_tetap').append('<span>' + result['rasio_perputaran_aktiva_tetap'] + '</span>');
                $('#rasio_perputaran_total_aktiva').empty();
                $('#rasio_perputaran_total_aktiva').append('<span>' + result['rasio_perputaran_total_aktiva'] + '</span>');
                $('#rasio_margin_laba_kotor').empty();
                $('#rasio_margin_laba_kotor').append('<span>' + result['rasio_margin_laba_kotor'] + '</span>');
                $('#rasio_margin_laba_bersih').empty();
                $('#rasio_margin_laba_bersih').append('<span>' + result['rasio_margin_laba_bersih'] + '</span>');
                $('#rasio_margin_laba_operasi').empty();
                $('#rasio_margin_laba_operasi').append('<span>' + result['rasio_margin_laba_operasi'] + '</span>');
                $('#return_on_investment').empty();
                $('#return_on_investment').append('<span>' + result['return_on_investment'] + '</span>');
                $('#return_on_assets').empty();
                $('#return_on_assets').append('<span>' + result['return_on_assets'] + '</span>');
                
                // $('#top_diagnosa_table_body').empty();
                // $('#top_diagnosa_table_body').empty();
                // result['top_diagnosa'].forEach(d => {
                //     $('#top_diagnosa_table_body').append('<tr><td>'+ d['diagnosa'] +'</td><td>'+ d['count'] +'</td></tr>')
                // });
            });
            return $.when(def1);
        },

        onclick_this_week: function (ev) {
            var self = this;
            var def1 = this._rpc({
                model: 'analisa.keuangan',
                method: 'get_dashboard_value',
                args: ['week'],
            }).then(function (result) {
                $('#rasio_hutang').empty();
                $('#rasio_hutang').append('<span>' + result['rasio_hutang'] + '</span>');
                $('#rasio_hutang_pendekatan_modal').empty();
                $('#rasio_hutang_pendekatan_modal').append('<span>' + result['rasio_hutang_pendekatan_modal'] + '</span>');
                $('#rasio_lancar').empty();
                $('#rasio_lancar').append('<span>' + result['rasio_lancar'] + '</span>');
                $('#rasio_kas').empty();
                $('#rasio_kas').append('<span>' + result['rasio_kas'] + '</span>');
                $('#rasio_cepat').empty();
                $('#rasio_cepat').append('<span>' + result['rasio_cepat'] + '</span>');
                $('#rasio_perputaran_persediaan').empty();
                $('#rasio_perputaran_persediaan').append('<span>' + result['rasio_perputaran_persediaan'] + '</span>');
                $('#rasio_perputaran_piutang').empty();
                $('#rasio_perputaran_piutang').append('<span>' + result['rasio_perputaran_piutang'] + '</span>');
                $('#rasio_perputaran_aktiva_tetap').empty();
                $('#rasio_perputaran_aktiva_tetap').append('<span>' + result['rasio_perputaran_aktiva_tetap'] + '</span>');
                $('#rasio_perputaran_total_aktiva').empty();
                $('#rasio_perputaran_total_aktiva').append('<span>' + result['rasio_perputaran_total_aktiva'] + '</span>');
                $('#rasio_margin_laba_kotor').empty();
                $('#rasio_margin_laba_kotor').append('<span>' + result['rasio_margin_laba_kotor'] + '</span>');
                $('#rasio_margin_laba_bersih').empty();
                $('#rasio_margin_laba_bersih').append('<span>' + result['rasio_margin_laba_bersih'] + '</span>');
                $('#rasio_margin_laba_operasi').empty();
                $('#rasio_margin_laba_operasi').append('<span>' + result['rasio_margin_laba_operasi'] + '</span>');
                $('#return_on_investment').empty();
                $('#return_on_investment').append('<span>' + result['return_on_investment'] + '</span>');
                $('#return_on_assets').empty();
                $('#return_on_assets').append('<span>' + result['return_on_assets'] + '</span>');
                
                // $('#top_diagnosa_table_body').empty();
                // result['top_diagnosa'].forEach(d => {
                //     $('#top_diagnosa_table_body').append('<tr><td>'+ d['diagnosa'] +'</td><td>'+ d['count'] +'</td></tr>')
                // });
            });
            return $.when(def1);
        },

        onclick_this_day: function (ev) {
            var self = this;
            var def1 = this._rpc({
                model: 'analisa.keuangan',
                method: 'get_dashboard_value',
                args: ['day'],
            }).then(function (result) {
                $('#rasio_hutang').empty();
                $('#rasio_hutang').append('<span>' + result['rasio_hutang'] + '</span>');
                $('#rasio_hutang_pendekatan_modal').empty();
                $('#rasio_hutang_pendekatan_modal').append('<span>' + result['rasio_hutang_pendekatan_modal'] + '</span>');
                $('#rasio_lancar').empty();
                $('#rasio_lancar').append('<span>' + result['rasio_lancar'] + '</span>');
                $('#rasio_kas').empty();
                $('#rasio_kas').append('<span>' + result['rasio_kas'] + '</span>');
                $('#rasio_cepat').empty();
                $('#rasio_cepat').append('<span>' + result['rasio_cepat'] + '</span>');
                $('#rasio_perputaran_persediaan').empty();
                $('#rasio_perputaran_persediaan').append('<span>' + result['rasio_perputaran_persediaan'] + '</span>');
                $('#rasio_perputaran_piutang').empty();
                $('#rasio_perputaran_piutang').append('<span>' + result['rasio_perputaran_piutang'] + '</span>');
                $('#rasio_perputaran_aktiva_tetap').empty();
                $('#rasio_perputaran_aktiva_tetap').append('<span>' + result['rasio_perputaran_aktiva_tetap'] + '</span>');
                $('#rasio_perputaran_total_aktiva').empty();
                $('#rasio_perputaran_total_aktiva').append('<span>' + result['rasio_perputaran_total_aktiva'] + '</span>');
                $('#rasio_margin_laba_kotor').empty();
                $('#rasio_margin_laba_kotor').append('<span>' + result['rasio_margin_laba_kotor'] + '</span>');
                $('#rasio_margin_laba_bersih').empty();
                $('#rasio_margin_laba_bersih').append('<span>' + result['rasio_margin_laba_bersih'] + '</span>');
                $('#rasio_margin_laba_operasi').empty();
                $('#rasio_margin_laba_operasi').append('<span>' + result['rasio_margin_laba_operasi'] + '</span>');
                $('#return_on_investment').empty();
                $('#return_on_investment').append('<span>' + result['return_on_investment'] + '</span>');
                $('#return_on_assets').empty();
                $('#return_on_assets').append('<span>' + result['return_on_assets'] + '</span>');
                
                // $('#top_diagnosa_table_body').empty();
                // result['top_diagnosa'].forEach(d => {
                //     $('#top_diagnosa_table_body').append('<tr><td>'+ d['diagnosa'] +'</td><td>'+ d['count'] +'</td></tr>')
                // });
            });
            return $.when(def1);
        },

        // render_pasien_perbulan_graph:function(){
        //     var self = this
        //     var ctx = self.$(".pasien_perbulan_graph");
        //     var def1 = this._rpc({
        //         model: 'custom.dashboard',
        //         method: 'get_pasien_perbulan_pie',
        //         // args: [],
        //     }).then(function (arrays) {
        //         var data = {
        //             labels : arrays[1],
        //             datasets: [{
        //                 label: "",
        //                 data: arrays[0],
        //                 backgroundColor: [
        //                     "#003f5c",
        //                     "#2f4b7c",
        //                     "#f95d6a",
        //                     "#665191",
        //                     "#d45087",
        //                     "#ff7c43",
        //                     "#ffa600",
        //                     "#a05195",
        //                     "#6d5c16"
        //                 ],
        //                 borderColor: [
        //                     "#003f5c",
        //                     "#2f4b7c",
        //                     "#f95d6a",
        //                     "#665191",
        //                     "#d45087",
        //                     "#ff7c43",
        //                     "#ffa600",
        //                     "#a05195",
        //                     "#6d5c16"
        //                 ],
        //                 borderWidth: 1
        //             },]
        //         };

        //         //options
        //         var options = {
        //             responsive: true,
        //             title: false,
        //             legend: {
        //                 display: true,
        //                 position: "right",
        //                 labels: {
        //                     fontColor: "#333",
        //                     fontSize: 16
        //                 }
        //             },
        //             scales: {
        //                 yAxes: [{
        //                     gridLines: {
        //                         color: "rgba(0, 0, 0, 0)",
        //                         display: false,
        //                     },
        //                     ticks: {
        //                         min: 0,
        //                         display: false,
        //                     }
        //                 }]
        //             }
        //         };

        //         //create Chart class object
        //         var chart = new Chart(ctx, {
        //             type: "doughnut",
        //             data: data,
        //             options: options
        //         });
        //     });
        // },

        // onclick_pasien_last_12months: function(ev) {
        //     var self = this;
        //     self.initial_render = true;
        //     var def1 = this._rpc({
        //         model: 'custom.dashboard',
        //         method: 'get_total_pasien_bar_chart',
        //         args: ['12']
        //     }).then(function(result){
        //         var ctx = document.getElementById("canvas_pasien_graph").getContext('2d');
        //         // Define the data
        //         var lost_reason = result.month // Add data values to array
        //         var count = result.count;
        //         var myChart = new Chart(ctx, {
        //             type: 'bar',
        //             data: {
        //                 labels: lost_reason,//x axis
        //                 datasets: [{
        //                     label: 'Count', // Name the series
        //                     data: count, // Specify the data values array
        //                     backgroundColor: '#66aecf',
        //                     borderColor: '#66aecf',
        //                     barPercentage: 0.5,
        //                     barThickness: 6,
        //                     maxBarThickness: 8,
        //                     minBarLength: 0,
        //                     borderWidth: 1, // Specify bar border width
        //                     type: 'bar', // Set this data to a line chart
        //                     fill: false
        //                 }]
        //             },
        //             options: {
        //                 scales: {
        //                     y: {
        //                         beginAtZero: true
        //                     },
        //                 },
        //                 responsive: true, // Instruct chart js to respond nicely.
        //                 maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
        //             }
        //         });
        //     });
        // },

        // rasio_hutang: function(e) {
        //     let value = $('#income_expense_values').val();
        //     let period
        //     if (value=="this_year"){
        //         period = 'year'
        //     }else if (value=="this_month"){
        //         period = 'month'
        //     }else if (value=="this_week"){
        //         period = 'week'
        //     }else if (value=="this_day"){
        //         period = 'day'
        //     }
        //     // console.log(period)

        //     var self = this;
        //     e.stopPropagation();
        //     e.preventDefault();
        //     var options = {
        //         on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        //     };
        //     this._rpc({
        //         model: 'analisa.keuangan',
        //         method: 'get_rasio_hutang',
        //         args: [period,true],
        //     }).then(function (result) {
        //         self.do_action({
        //             name: result['name'],
        //             type: result['type'],
        //             res_model: result['res_model'],
        //             view_mode: result['view_mode'],
        //             views: result['views'],
        //             domain: result['domain'],
        //             context: result['context'],
        //             target: result['target'],
        //         }, options)
        //     })
        // },

        // rasio_hutang_pendekatan_modal: function(e) {
        //     let value = $('#income_expense_values').val();
        //     let period
        //     if (value=="this_year"){
        //         period = 'year'
        //     }else if (value=="this_month"){
        //         period = 'month'
        //     }else if (value=="this_week"){
        //         period = 'week'
        //     }else if (value=="this_day"){
        //         period = 'day'
        //     }
        //     // console.log(period)

        //     var self = this;
        //     e.stopPropagation();
        //     e.preventDefault();
        //     var options = {
        //         on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        //     };
        //     this._rpc({
        //         model: 'analisa.keuangan',
        //         method: 'get_rasio_hutang_pendekatan_modal',
        //         args: [period,true],
        //     }).then(function (result) {
        //         self.do_action({
        //             name: result['name'],
        //             type: result['type'],
        //             res_model: result['res_model'],
        //             view_mode: result['view_mode'],
        //             views: result['views'],
        //             domain: result['domain'],
        //             context: result['context'],
        //             target: result['target'],
        //         }, options)
        //     })
        // },

        // rasio_lancar: function(e) {
        //     let value = $('#income_expense_values').val();
        //     let period
        //     if (value=="this_year"){
        //         period = 'year'
        //     }else if (value=="this_month"){
        //         period = 'month'
        //     }else if (value=="this_week"){
        //         period = 'week'
        //     }else if (value=="this_day"){
        //         period = 'day'
        //     }
        //     // console.log(period)

        //     var self = this;
        //     e.stopPropagation();
        //     e.preventDefault();
        //     var options = {
        //         on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        //     };
        //     this._rpc({
        //         model: 'analisa.keuangan',
        //         method: 'get_rasio_lancar',
        //         args: [period,true],
        //     }).then(function (result) {
        //         self.do_action({
        //             name: result['name'],
        //             type: result['type'],
        //             res_model: result['res_model'],
        //             view_mode: result['view_mode'],
        //             views: result['views'],
        //             domain: result['domain'],
        //             context: result['context'],
        //             target: result['target'],
        //         }, options)
        //     })
        // },

        // rasio_kas: function(e) {
        //     let value = $('#income_expense_values').val();
        //     let period
        //     if (value=="this_year"){
        //         period = 'year'
        //     }else if (value=="this_month"){
        //         period = 'month'
        //     }else if (value=="this_week"){
        //         period = 'week'
        //     }else if (value=="this_day"){
        //         period = 'day'
        //     }
        //     // console.log(period)

        //     var self = this;
        //     e.stopPropagation();
        //     e.preventDefault();
        //     var options = {
        //         on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        //     };
        //     this._rpc({
        //         model: 'analisa.keuangan',
        //         method: 'get_rasio_kas',
        //         args: [period,true],
        //     }).then(function (result) {
        //         self.do_action({
        //             name: result['name'],
        //             type: result['type'],
        //             res_model: result['res_model'],
        //             view_mode: result['view_mode'],
        //             views: result['views'],
        //             domain: result['domain'],
        //             context: result['context'],
        //             target: result['target'],
        //         }, options)
        //     })
        // },

        // rasio_cepat: function(e) {
        //     let value = $('#income_expense_values').val();
        //     let period
        //     if (value=="this_year"){
        //         period = 'year'
        //     }else if (value=="this_month"){
        //         period = 'month'
        //     }else if (value=="this_week"){
        //         period = 'week'
        //     }else if (value=="this_day"){
        //         period = 'day'
        //     }
        //     // console.log(period)

        //     var self = this;
        //     e.stopPropagation();
        //     e.preventDefault();
        //     var options = {
        //         on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        //     };
        //     this._rpc({
        //         model: 'analisa.keuangan',
        //         method: 'get_rasio_cepat',
        //         args: [period,true],
        //     }).then(function (result) {
        //         self.do_action({
        //             name: result['name'],
        //             type: result['type'],
        //             res_model: result['res_model'],
        //             view_mode: result['view_mode'],
        //             views: result['views'],
        //             domain: result['domain'],
        //             context: result['context'],
        //             target: result['target'],
        //         }, options)
        //     })
        // },

        // rasio_perputaran_persediaan: function(e) {
        //     let value = $('#income_expense_values').val();
        //     let period
        //     if (value=="this_year"){
        //         period = 'year'
        //     }else if (value=="this_month"){
        //         period = 'month'
        //     }else if (value=="this_week"){
        //         period = 'week'
        //     }else if (value=="this_day"){
        //         period = 'day'
        //     }
        //     // console.log(period)

        //     var self = this;
        //     e.stopPropagation();
        //     e.preventDefault();
        //     var options = {
        //         on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        //     };
        //     this._rpc({
        //         model: 'analisa.keuangan',
        //         method: 'get_rasio_perputaran_persediaan',
        //         args: [period,true],
        //     }).then(function (result) {
        //         self.do_action({
        //             name: result['name'],
        //             type: result['type'],
        //             res_model: result['res_model'],
        //             view_mode: result['view_mode'],
        //             views: result['views'],
        //             domain: result['domain'],
        //             context: result['context'],
        //             target: result['target'],
        //         }, options)
        //     })
        // },

        // rasio_perputaran_piutang: function(e) {
        //     let value = $('#income_expense_values').val();
        //     let period
        //     if (value=="this_year"){
        //         period = 'year'
        //     }else if (value=="this_month"){
        //         period = 'month'
        //     }else if (value=="this_week"){
        //         period = 'week'
        //     }else if (value=="this_day"){
        //         period = 'day'
        //     }
        //     // console.log(period)

        //     var self = this;
        //     e.stopPropagation();
        //     e.preventDefault();
        //     var options = {
        //         on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        //     };
        //     this._rpc({
        //         model: 'analisa.keuangan',
        //         method: 'get_rasio_perputaran_piutang',
        //         args: [period,true],
        //     }).then(function (result) {
        //         self.do_action({
        //             name: result['name'],
        //             type: result['type'],
        //             res_model: result['res_model'],
        //             view_mode: result['view_mode'],
        //             views: result['views'],
        //             domain: result['domain'],
        //             context: result['context'],
        //             target: result['target'],
        //         }, options)
        //     })
        // },

        // rasio_perputaran_aktiva_tetap: function(e) {
        //     let value = $('#income_expense_values').val();
        //     let period
        //     if (value=="this_year"){
        //         period = 'year'
        //     }else if (value=="this_month"){
        //         period = 'month'
        //     }else if (value=="this_week"){
        //         period = 'week'
        //     }else if (value=="this_day"){
        //         period = 'day'
        //     }
        //     // console.log(period)

        //     var self = this;
        //     e.stopPropagation();
        //     e.preventDefault();
        //     var options = {
        //         on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        //     };
        //     this._rpc({
        //         model: 'analisa.keuangan',
        //         method: 'get_rasio_perputaran_aktiva_tetap',
        //         args: [period,true],
        //     }).then(function (result) {
        //         self.do_action({
        //             name: result['name'],
        //             type: result['type'],
        //             res_model: result['res_model'],
        //             view_mode: result['view_mode'],
        //             views: result['views'],
        //             domain: result['domain'],
        //             context: result['context'],
        //             target: result['target'],
        //         }, options)
        //     })
        // },

        // rasio_perputaran_total_aktiva: function(e) {
        //     let value = $('#income_expense_values').val();
        //     let period
        //     if (value=="this_year"){
        //         period = 'year'
        //     }else if (value=="this_month"){
        //         period = 'month'
        //     }else if (value=="this_week"){
        //         period = 'week'
        //     }else if (value=="this_day"){
        //         period = 'day'
        //     }
        //     // console.log(period)

        //     var self = this;
        //     e.stopPropagation();
        //     e.preventDefault();
        //     var options = {
        //         on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        //     };
        //     this._rpc({
        //         model: 'analisa.keuangan',
        //         method: 'get_rasio_perputaran_total_aktiva',
        //         args: [period,true],
        //     }).then(function (result) {
        //         self.do_action({
        //             name: result['name'],
        //             type: result['type'],
        //             res_model: result['res_model'],
        //             view_mode: result['view_mode'],
        //             views: result['views'],
        //             domain: result['domain'],
        //             context: result['context'],
        //             target: result['target'],
        //         }, options)
        //     })
        // },

        // rasio_margin_laba_kotor: function(e) {
        //     let value = $('#income_expense_values').val();
        //     let period
        //     if (value=="this_year"){
        //         period = 'year'
        //     }else if (value=="this_month"){
        //         period = 'month'
        //     }else if (value=="this_week"){
        //         period = 'week'
        //     }else if (value=="this_day"){
        //         period = 'day'
        //     }
        //     // console.log(period)

        //     var self = this;
        //     e.stopPropagation();
        //     e.preventDefault();
        //     var options = {
        //         on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        //     };
        //     this._rpc({
        //         model: 'analisa.keuangan',
        //         method: 'get_rasio_margin_laba_kotor',
        //         args: [period,true],
        //     }).then(function (result) {
        //         self.do_action({
        //             name: result['name'],
        //             type: result['type'],
        //             res_model: result['res_model'],
        //             view_mode: result['view_mode'],
        //             views: result['views'],
        //             domain: result['domain'],
        //             context: result['context'],
        //             target: result['target'],
        //         }, options)
        //     })
        // },

        // rasio_margin_laba_bersih: function(e) {
        //     let value = $('#income_expense_values').val();
        //     let period
        //     if (value=="this_year"){
        //         period = 'year'
        //     }else if (value=="this_month"){
        //         period = 'month'
        //     }else if (value=="this_week"){
        //         period = 'week'
        //     }else if (value=="this_day"){
        //         period = 'day'
        //     }
        //     // console.log(period)

        //     var self = this;
        //     e.stopPropagation();
        //     e.preventDefault();
        //     var options = {
        //         on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        //     };
        //     this._rpc({
        //         model: 'analisa.keuangan',
        //         method: 'get_rasio_margin_laba_bersih',
        //         args: [period,true],
        //     }).then(function (result) {
        //         self.do_action({
        //             name: result['name'],
        //             type: result['type'],
        //             res_model: result['res_model'],
        //             view_mode: result['view_mode'],
        //             views: result['views'],
        //             domain: result['domain'],
        //             context: result['context'],
        //             target: result['target'],
        //         }, options)
        //     })
        // },

        // rasio_margin_laba_operasi: function(e) {
        //     let value = $('#income_expense_values').val();
        //     let period
        //     if (value=="this_year"){
        //         period = 'year'
        //     }else if (value=="this_month"){
        //         period = 'month'
        //     }else if (value=="this_week"){
        //         period = 'week'
        //     }else if (value=="this_day"){
        //         period = 'day'
        //     }
        //     // console.log(period)

        //     var self = this;
        //     e.stopPropagation();
        //     e.preventDefault();
        //     var options = {
        //         on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        //     };
        //     this._rpc({
        //         model: 'analisa.keuangan',
        //         method: 'get_rasio_margin_laba_operasi',
        //         args: [period,true],
        //     }).then(function (result) {
        //         self.do_action({
        //             name: result['name'],
        //             type: result['type'],
        //             res_model: result['res_model'],
        //             view_mode: result['view_mode'],
        //             views: result['views'],
        //             domain: result['domain'],
        //             context: result['context'],
        //             target: result['target'],
        //         }, options)
        //     })
        // },

        // return_on_investment: function(e) {
        //     let value = $('#income_expense_values').val();
        //     let period
        //     if (value=="this_year"){
        //         period = 'year'
        //     }else if (value=="this_month"){
        //         period = 'month'
        //     }else if (value=="this_week"){
        //         period = 'week'
        //     }else if (value=="this_day"){
        //         period = 'day'
        //     }
        //     // console.log(period)

        //     var self = this;
        //     e.stopPropagation();
        //     e.preventDefault();
        //     var options = {
        //         on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        //     };
        //     this._rpc({
        //         model: 'analisa.keuangan',
        //         method: 'get_return_on_investment',
        //         args: [period,true],
        //     }).then(function (result) {
        //         self.do_action({
        //             name: result['name'],
        //             type: result['type'],
        //             res_model: result['res_model'],
        //             view_mode: result['view_mode'],
        //             views: result['views'],
        //             domain: result['domain'],
        //             context: result['context'],
        //             target: result['target'],
        //         }, options)
        //     })
        // },

        // return_on_assets: function(e) {
        //     let value = $('#income_expense_values').val();
        //     let period
        //     if (value=="this_year"){
        //         period = 'year'
        //     }else if (value=="this_month"){
        //         period = 'month'
        //     }else if (value=="this_week"){
        //         period = 'week'
        //     }else if (value=="this_day"){
        //         period = 'day'
        //     }
        //     // console.log(period)

        //     var self = this;
        //     e.stopPropagation();
        //     e.preventDefault();
        //     var options = {
        //         on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        //     };
        //     this._rpc({
        //         model: 'analisa.keuangan',
        //         method: 'get_return_on_assets',
        //         args: [period,true],
        //     }).then(function (result) {
        //         self.do_action({
        //             name: result['name'],
        //             type: result['type'],
        //             res_model: result['res_model'],
        //             view_mode: result['view_mode'],
        //             views: result['views'],
        //             domain: result['domain'],
        //             context: result['context'],
        //             target: result['target'],
        //         }, options)
        //     })
        // },

        on_reverse_breadcrumb: function() {
            var self = this;
            web_client.do_push_state({});
            this.update_cp();
            this.fetch_data()
        },

        update_cp: function() {
        var self = this;
        },
    })
    core.action_registry.add('custom_dashboard_tags', AnalisaKeuanganDashboard);
    return AnalisaKeuanganDashboard;
})