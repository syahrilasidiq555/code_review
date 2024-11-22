odoo.define('custom_pos.ClientListScreen', function(require) {
	"use strict";

	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');
	let rpc = require('web.rpc');
	const ClientListScreen = require('point_of_sale.ClientListScreen'); 

	const RDCClientListScreen = (ClientListScreen) =>
	class extends ClientListScreen {
		constructor() {
			super(...arguments);
		}

		async getNewClient() {
            var domain = [];
            if(this.state.query) {
                domain = [
                    ['is_jenazah','=',true],
                    ['is_still_semayam','=',true],
                    '|',
                    ["display_name", "ilike", this.state.query],
                    ["email", "ilike", this.state.query],
                    ];
            }
            domain = [['is_jenazah','=',true],['is_still_semayam','=',true]]
            console.log(domain)
            var fields = _.find(this.env.pos.models, function(model){ return model.label === 'load_partners'; }).fields;
            var result = await this.rpc({
                model: 'res.partner',
                method: 'search_read',
                args: [domain, fields],
                kwargs: {
                    limit: 10,
                },
            },{
                timeout: 3000,
                shadow: true,
            });

            return result;
        }

	};

	Registries.Component.extend(ClientListScreen, RDCClientListScreen);

	return ClientListScreen;
});