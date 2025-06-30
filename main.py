from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper
app = FastAPI()

inprogress_orders = {}

@app.get("/")
def health_check():
    return {"status": "API is running"}

@app.post("/")
async def handle_request(request: Request):
    payload = await request.json()

    parameters = payload.get('queryResult', {}).get('parameters', {})

    # Extract fields from Dialogflow payload
    intent = payload.get('queryResult', {}).get('intent', {}).get('displayName', '')
    parameters = payload.get('queryResult', {}).get('parameters', {})
    output_contexts = payload.get('queryResult', {}).get('outputContexts', [])

    session_id = generic_helper.extract_session_id(output_contexts[0]['name'])



    intent_handler_dict = {
        'track.order - context: ongoing-order' : track_order,
        'order.add - context: ongoing-order' : add_to_order,
        'order.complete - context: ongoing-order' : complete_order,
        'order.remove - context: ongoing-order' : remove_from_order
    }

    handler = intent_handler_dict.get(intent)

    if handler:
        return handler(parameters, session_id)
    else:
        return JSONResponse(content={
            "fulfillmentText": "Sorry, I couldn't understand your request."
        })


def add_to_order(parameters: dict, session_id: str):
    print("[DEBUG] Parameters received in add_to_order:", parameters) #debug

    med_items = parameters.get('med_item')
    quantities = parameters.get('number')

    if len(med_items) != len(quantities):
        fulfillment_text = "Please make sure to provide a quantity for each item."
    else:
        new_item_dict = dict(zip(med_items, quantities))


        if session_id in inprogress_orders:
            inprogress_orders[session_id].update(new_item_dict)

        else:
            inprogress_orders[session_id] = new_item_dict

        order_str = generic_helper.get_str_from_item_dict(inprogress_orders[session_id])

        fulfillment_text = f"So far you have this order: {order_str}. Do you need anything else?"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def  save_to_db(order: dict):
    next_order_id = db_helper.get_next_order_id()

    for med_item, quantity in order.items():
        rcode = db_helper.insert_order_item(
            med_item,
            quantity,
            next_order_id
        )
        if rcode == -1:
            return -1

    db_helper.insert_order_tracking(next_order_id, "inprogress")

    return next_order_id


def complete_order(parameters: dict, session_id : str):
    if session_id not in inprogress_orders:
        fulfillment_text = "Sorry, I having trouble finding your order. Please place a new order."
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)

        if order_id == -1:
            fulfillment_text = "Sorry I could not place your order. Please try again."

        else:
            order_total = db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Awesome! We have placed your order." \
                              f" Your order total is {order_total}." \
                              f"Your order id is {order_id}."
            
        del inprogress_orders[session_id]

    return JSONResponse(content={
        "fulfillmentText" : fulfillment_text
    })


def track_order(parameters: dict, session_id : str):
    order_id = parameters.get('number')

    if order_id is None:
        return JSONResponse(content={
            "fulfillmentText": "No order ID provided."
        })

    order_status = db_helper.get_order_status(order_id)

    if order_status:
        fulfillment_text = f"The order status for {int(order_id)} is: {order_status}."
    else:
        fulfillment_text = f"No order found for order ID {int(order_id)}."

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "Sorry, I could not find your order. Please try again."
        })
    current_order = inprogress_orders[session_id]
    med_items = parameters.get('med_item')

    removed_items = []
    no_such_items = []

    for item in med_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]

    if len(removed_items) > 0:
        fulfillment_text = f"We have removed {removed_items} from your order"

    if len(no_such_items) > 0:
        fulfillment_text = f"There is not such items as {no_such_items}"

    if len(current_order.keys()) == 0:
        fulfillment_text += "Your order is empty!"
    else:
        order_str = generic_helper.get_str_from_item_dict(current_order)
        fulfillment_text += f"Here's what's left in your order: {order_str}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })



