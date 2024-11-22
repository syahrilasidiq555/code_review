odoo.define('custom_pos.db_custom', function (require) {
    "use strict";
        var PosDB = require('point_of_sale.DB');
        PosDB.DB = PosDB.include({
            _partner_search_string: function(partner){
                var str =  partner.name || '';
                if(partner.barcode){
                    str += '|' + partner.barcode;
                }
                if(partner.address){
                    str += '|' + partner.address;
                }
                if(partner.phone){
                    str += '|' + partner.phone.split(' ').join('');
                }
                if(partner.mobile){
                    str += '|' + partner.mobile.split(' ').join('');
                }
                if(partner.email){
                    str += '|' + partner.email;
                }
                if(partner.vat){
                    str += '|' + partner.vat;
                }

                // syahril 28/12/23 : hanya tambah ini di tengah fungsinya
                if(partner.penanggungjawab){
                    str += '|' + partner.penanggungjawab;
                }
                if(partner.ruangan_id){
                    str += '|' + partner.ruangan_id[1];
                }
                // syahril 28/12/23 : end
                
                str = '' + partner.id + ':' + str.replace(':', '').replace(/\n/g, ' ') + '\n';
                return str;
            },
        });
    });
    