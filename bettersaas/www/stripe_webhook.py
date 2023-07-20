import frappe
import json
import stripe
from clientside.stripe import StripeSubscriptionManager
stripe_manager = StripeSubscriptionManager(country="IN")

    
@frappe.whitelist(allow_guest=True)
def handler(*args, **kwargs):
    payload = frappe.local.request.get_data()
    sig_header = frappe.local.request.headers['Stripe-Signature']
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_manager.endpoint_secret
        )
    except ValueError as e:
        print("invalid payload")
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print("invalid signature")
        raise e
    print("event type", event["type"])
    if event["type"] == "checkout.session.completed":
        stripe_manager.handle_checkout_session_completed(event)
        
    if event["type"] == "invoice.paid":
        stripe_manager.handle_invoice_paid(event)
    if event["type"] == "invoice.payment_action_required":
        # get invoice client secret
        stripe_manager.handle_payment_intent_action_required(event)
    if event["type"] =="payment_intent.payment_failed":
        stripe_manager.handle_payment_intent_failed()
        


    


    
