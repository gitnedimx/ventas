odoo.define('l10n_mx_edi_website.pos_ticket_number', function(require){
"use strict";

var models = require('point_of_sale.models');

var _super_order = models.Order.prototype;

models.Order = models.Order.extend({
    initialize: function() {
        _super_order.initialize.apply(this, arguments);
    this.ticket_number = Math.random().toString(32).substr(2) + Date.now();
    this.current_location = location.protocol + "//" + location.host;
    },
    export_for_printing: function(){
        var res = _super_order.export_for_printing.apply(this,arguments);
        res.ticket_number = this.ticket_number;
        return res;
    },
    export_as_JSON: function(){
        var res = _super_order.export_as_JSON.apply(this,arguments);
        res.ticket_number = this.ticket_number;
        return res;
    },
    init_from_JSON: function(json){
        _super_order.init_from_JSON.apply(this,arguments);
        this.ticket_number = json.ticket_number;
    },
});

});
