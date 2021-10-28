from unittest.mock import patch

from Adyen.client import AdyenResult
from django.core.exceptions import ValidationError

from ......payment import ChargeStatus
from ......payment.gateways.adyen.webhooks import handle_api_response


@patch("saleor.payment.gateway.refund")
@patch("saleor.payment.gateway.void")
def test_handle_api_response_auto_capture_order_created_can_refund(
    void_mock, refund_mock, payment_adyen_for_checkout, adyen_plugin
):
    payment_adyen_for_checkout.to_confirm = True
    payment_adyen_for_checkout.save(update_fields=["to_confirm"])

    plugin = adyen_plugin(adyen_auto_capture=True)

    adyen_response = AdyenResult(
        {
            "additionalData": {"paymentMethod": "visa"},
            "pspReference": "882635241694695D",
            "resultCode": "Authorised",
            "amount": {"currency": "USD", "value": 4211},
            "merchantReference": "UGF5bWVudDoxMDU=",
        }
    )

    handle_api_response(payment_adyen_for_checkout, adyen_response, plugin.channel.slug)

    payment_adyen_for_checkout.refresh_from_db()

    assert payment_adyen_for_checkout.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment_adyen_for_checkout.order
    assert payment_adyen_for_checkout.can_refund()
    assert not payment_adyen_for_checkout.can_void()
    assert refund_mock.call_count == 0
    assert void_mock.call_count == 0


@patch("saleor.payment.gateway.refund")
@patch("saleor.payment.gateway.void")
def test_handle_api_response_wo_auto_capture_order_created_can_void(
    void_mock, refund_mock, payment_adyen_for_checkout, adyen_plugin
):
    payment_adyen_for_checkout.to_confirm = True
    payment_adyen_for_checkout.save(update_fields=["to_confirm"])

    plugin = adyen_plugin()

    adyen_response = AdyenResult(
        {
            "additionalData": {"paymentMethod": "visa"},
            "pspReference": "882635241694695D",
            "resultCode": "Authorised",
            "amount": {"currency": "USD", "value": 4211},
            "merchantReference": "UGF5bWVudDoxMDU=",
        }
    )

    handle_api_response(payment_adyen_for_checkout, adyen_response, plugin.channel.slug)

    payment_adyen_for_checkout.refresh_from_db()

    assert payment_adyen_for_checkout.charge_status == ChargeStatus.NOT_CHARGED
    assert payment_adyen_for_checkout.order
    assert payment_adyen_for_checkout.can_void()
    assert not payment_adyen_for_checkout.can_refund()
    assert refund_mock.call_count == 0
    assert void_mock.call_count == 0


@patch("saleor.payment.gateway.void")
@patch("saleor.payment.gateway.refund")
@patch("saleor.checkout.complete_checkout._get_order_data")
def test_handle_api_response_wo_auto_capture_cannot_create_order_void_payment(
    order_data_mock, refund_mock, void_mock, payment_adyen_for_checkout, adyen_plugin
):
    order_data_mock.side_effect = ValidationError("Test error")
    payment_adyen_for_checkout.to_confirm = True
    payment_adyen_for_checkout.save(update_fields=["to_confirm"])

    plugin = adyen_plugin()

    adyen_response = AdyenResult(
        {
            "additionalData": {"paymentMethod": "visa"},
            "pspReference": "882635241694695D",
            "resultCode": "Authorised",
            "amount": {"currency": "USD", "value": 4211},
            "merchantReference": "UGF5bWVudDoxMDU=",
        }
    )

    handle_api_response(payment_adyen_for_checkout, adyen_response, plugin.channel.slug)

    payment_adyen_for_checkout.refresh_from_db()

    assert payment_adyen_for_checkout.charge_status == ChargeStatus.NOT_CHARGED
    assert not payment_adyen_for_checkout.order

    assert not payment_adyen_for_checkout.can_refund()
    assert refund_mock.call_count == 0

    assert payment_adyen_for_checkout.can_void()
    assert void_mock.call_count == 2


@patch("saleor.payment.gateway.void")
@patch("saleor.payment.gateway.refund")
@patch("saleor.checkout.complete_checkout._get_order_data")
def test_handle_api_response_auto_capture_cannot_create_order_refund_payment(
    order_data_mock, refund_mock, void_mock, payment_adyen_for_checkout, adyen_plugin
):
    order_data_mock.side_effect = ValidationError("Test error")
    payment_adyen_for_checkout.to_confirm = True
    payment_adyen_for_checkout.save(update_fields=["to_confirm"])

    plugin = adyen_plugin(adyen_auto_capture=True)

    adyen_response = AdyenResult(
        {
            "additionalData": {"paymentMethod": "visa"},
            "pspReference": "882635241694695D",
            "resultCode": "Authorised",
            "amount": {"currency": "USD", "value": 4211},
            "merchantReference": "UGF5bWVudDoxMDU=",
        }
    )

    handle_api_response(payment_adyen_for_checkout, adyen_response, plugin.channel.slug)

    payment_adyen_for_checkout.refresh_from_db()

    assert payment_adyen_for_checkout.charge_status == ChargeStatus.FULLY_CHARGED
    assert not payment_adyen_for_checkout.order

    assert payment_adyen_for_checkout.can_refund()
    assert refund_mock.call_count == 2

    assert not payment_adyen_for_checkout.can_void()
    assert void_mock.call_count == 0
