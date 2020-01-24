odoo.define('bi_branch_pos.pos_extended', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var popups = require('point_of_sale.popups');
    

    var QWeb = core.qweb;
    var _t = core._t;

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var session_model = _.find(this.models, function(model){ return model.model === 'pos.session'; });
            session_model.fields.push('branch_id');
            return _super_posmodel.initialize.call(this, session, attributes);
        },

    });
});
