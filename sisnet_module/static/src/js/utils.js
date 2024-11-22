odoo.define('rdc_module.utils', function(require) {
    'use strict';
    var core = require('web.core');
    var formatNumber = function(value) {
        var thousandsSep = core._t.database.parameters.thousands_sep || ',';
        var decimalSep = core._t.database.parameters.decimal_point || '.';
        var str = String(value).trim();
        var sign = str.startsWith('-') ? '-' : '';
        str = str.replace(new RegExp('[^' + decimalSep + '\\d]','g'), '');
        str = str.replace(new RegExp('^\\' + decimalSep + '*'), '')
        str = str.replace(/\B(?=((\d{3})+(?!\d)))/g, thousandsSep);
        var splits = str.split(decimalSep);
        if (splits.length > 1) {
            str = splits[0] + decimalSep + splits[1].replace(new RegExp('\\' + thousandsSep,'g'), '');
        }
        str = sign + str;
        return str
    };
    var formatFormula = function(formula) {
        if (!formula.startsWith('=')) {
            return formatNumber(formula);
        }
        var str = '';
        for (let v of formula.split(new RegExp(/([-+*/()^=\s])/g))) {
            if (!['+', '-', '*', '/', '(', ')', '^', '='].includes(v) && v.trim()) {
                v = formatNumber(v);
            }
            str += v;
        }
        return str;
    }
    var parseNumber = function(value) {
        var thousandsSep = core._t.database.parameters.thousands_sep || ',';
        var decimalSep = core._t.database.parameters.decimal_point || '.';
        var str = value;
        str = str.replace(new RegExp('\\' + thousandsSep,'g'), '');
        str = str.replace(decimalSep, '.');
        return Number(str);
    }
    return {
        formatNumber: formatNumber,
        formatFormula: formatFormula,
        parseNumber: parseNumber
    }
});