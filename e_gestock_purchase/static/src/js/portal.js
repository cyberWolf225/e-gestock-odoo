/* Javascript pour le portail fournisseur E-GESTOCK */
odoo.define('e_gestock_purchase.portal', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;

    publicWidget.registry.EGestockPurchasePortal = publicWidget.Widget.extend({
        selector: '.e_gestock_supplier_portal',
        events: {
            'change .js-quantity-field': '_onChangeQuantity',
            'change .js-price-field': '_onChangePrice',
            'change .js-discount-field': '_onChangeDiscount',
        },

        /**
         * @override
         */
        start: function () {
            var def = this._super.apply(this, arguments);
            this._updateTotals();
            return def;
        },

        /**
         * Appelé lorsqu'une quantité est modifiée
         * @private
         * @param {Event} ev
         */
        _onChangeQuantity: function (ev) {
            this._updateLineTotal(ev.currentTarget.closest('tr'));
            this._updateTotals();
        },

        /**
         * Appelé lorsqu'un prix est modifié
         * @private
         * @param {Event} ev
         */
        _onChangePrice: function (ev) {
            this._updateLineTotal(ev.currentTarget.closest('tr'));
            this._updateTotals();
        },

        /**
         * Appelé lorsqu'une remise est modifiée
         * @private
         * @param {Event} ev
         */
        _onChangeDiscount: function (ev) {
            this._updateLineTotal(ev.currentTarget.closest('tr'));
            this._updateTotals();
        },

        /**
         * Met à jour le total d'une ligne
         * @private
         * @param {HTMLElement} row
         */
        _updateLineTotal: function (row) {
            var quantity = parseFloat($(row).find('.js-quantity-field').val() || 0);
            var price = parseFloat($(row).find('.js-price-field').val() || 0);
            var discount = parseFloat($(row).find('.js-discount-field').val() || 0);
            
            var total = quantity * price * (1 - discount / 100);
            $(row).find('.js-line-total').text(this._formatCurrency(total));
            $(row).find('.js-line-total-input').val(total);
        },

        /**
         * Met à jour les totaux globaux
         * @private
         */
        _updateTotals: function () {
            var self = this;
            var totalHT = 0;
            
            $('.js-line-total-input').each(function () {
                totalHT += parseFloat($(this).val() || 0);
            });
            
            var globalDiscount = parseFloat($('.js-global-discount').val() || 0);
            var totalHTAfterDiscount = totalHT * (1 - globalDiscount / 100);
            
            var vatRate = parseFloat($('.js-vat-rate').val() || 0);
            var vatAmount = totalHTAfterDiscount * vatRate / 100;
            var totalTTC = totalHTAfterDiscount + vatAmount;
            
            $('.js-total-ht').text(this._formatCurrency(totalHT));
            $('.js-total-ht-after-discount').text(this._formatCurrency(totalHTAfterDiscount));
            $('.js-vat-amount').text(this._formatCurrency(vatAmount));
            $('.js-total-ttc').text(this._formatCurrency(totalTTC));
            
            // Mise à jour des champs cachés
            $('.js-total-ht-input').val(totalHT);
            $('.js-total-ht-after-discount-input').val(totalHTAfterDiscount);
            $('.js-vat-amount-input').val(vatAmount);
            $('.js-total-ttc-input').val(totalTTC);
        },

        /**
         * Formatte une valeur monétaire
         * @private
         * @param {number} value
         * @returns {string}
         */
        _formatCurrency: function (value) {
            return value.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$& ');
        }
    });

    return publicWidget.registry.EGestockPurchasePortal;
}); 