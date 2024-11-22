// bi_pos_warehouse_management js
odoo.define('custom_pos.pos', function(require) {
	"use strict";

	var models = require('point_of_sale.models');
	var session = require('web.session');
	
	// console.log(models.PosModel)
	// console.log("+++++++++++++++++++++")
	// console.log(models.PosModel.prototype.models)
	
	// models.load_fields('res.partner', ['ruangan_id','paket_id','child_ids','tanggal_kedatangan','penanggungjawab']);

	var proto_models = models.PosModel.prototype.models;
    // for(var i=0; i < proto_models.length; i++){
    //     var model = proto_models[i];
    //     if(model.model === 'res.partner'){
	// 		model.fields.push('ruangan_id','paket_id','last_sale_invoice_status','child_ids','tanggal_kedatangan','penanggungjawab');
	// 		model.domain = async function(self){
	// 			if(self.config.limited_partners_loading) {
	// 				const result = await self.rpc({
	// 					model: 'pos.config',
	// 					method: 'get_limited_partners_loading',
	// 					args: [self.config.id],
	// 				});
	// 				return [['is_jenazah','=',true],['last_sale_invoice_status','in',['draft','posted','none']],['id','in', result.map(elem => elem[0])]];
	// 			}
	// 			return [['is_jenazah','=',true],['last_sale_invoice_status','in',['draft','posted','none']]];
	// 		}
	// 	} 
    // }

	for(var i=0; i < proto_models.length; i++){
        var model = proto_models[i];
        if(model.model === 'res.partner'){
			model.fields.push('ruangan_id','paket_id','is_still_semayam','child_ids','tanggal_kedatangan','penanggungjawab');
			model.domain = async function(self){
				if(self.config.limited_partners_loading) {
					const result = await self.rpc({
						model: 'pos.config',
						method: 'get_limited_partners_loading',
						args: [self.config.id],
					});
					return [['is_jenazah','=',true],['is_still_semayam','=',true],['id','in', result.map(elem => elem[0])]];
				}
				return [['is_jenazah','=',true],['is_still_semayam','=',true]];
			}
		} 
    }

});
