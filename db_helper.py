import sys

import mysql.connector
global cnx

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="ds260705",
        database="pandeyji_eatery"
    )

def insert_order_item(med_items, quantity, order_id):
    try :
        cnx = get_connection()
        cursor = cnx.cursor()

        cursor.callproc('insert_order_item', (med_items, quantity, order_id))

        cnx.commit()
        cursor.close()

        print("Order Item Inserted")
        return 1

    except mysql.connector.Error as err:
        print(f"Error insterting order item: {err}")

        cnx.rollback()
        return -1

    except Exception as e:
        print("Unexpected error:", {e})
        cnx.rollback()
        return -1

def get_total_order_price(order_id):
    cnx = get_connection()
    cursor = cnx.cursor()

    query = f"SELECT get_total_order_price({order_id})"
    cursor.execute(query)

    result = cursor.fetchone()[0]

    cursor.close()

    return result



def get_next_order_id():
    cnx = get_connection()
    cursor = cnx.cursor()

    query = f"SELECT MAX(order_id) FROM orders"

    cursor.execute(query)
    result = cursor.fetchone()[0]
    cursor.close()

    if result is None:
        return 1
    else:
        return result + 1


def insert_order_tracking(order_id, status):
    cnx = get_connection()
    cursor = cnx.cursor()
    query = f'INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)'

    cursor.execute(query, (order_id, status))
    cnx.commit()
    cursor.close()




def get_order_status(order_id):
    try:
        order_id = str(order_id).strip()
        cnx = get_connection()

        cursor = cnx.cursor()
        query = f"SELECT status FROM order_tracking WHERE order_id = %s"
        cursor.execute(query, (order_id,))
        result = cursor.fetchone()

        cursor.close()

        if result:
            return result[0]
        else:
            return None

    except mysql.connector.Error as err:
        return None
