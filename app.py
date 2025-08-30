import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import firebase_admin
from firebase_admin import credentials, auth, firestore, messaging
import os, time
from datetime import datetime


# Load the service account key
path_dev = "config/config.json"
path_prod = "/etc/secrets/config.json"

cred = credentials.Certificate(path_prod)
firebase_admin.initialize_app(cred)

# Now you can use Firestore, Auth, etc.
db = firestore.client()


app = Flask(__name__)
CORS(app)
headers = {
    "Authorization": "Token f0f88d1253d5855bceb565ba5696e7c5e77eaa823a3611249e9d1d386f17",
    "Content-Type": "application/json"
}

headers2 = {
    "Authorization": "Bearer FLWSECK-020dd7d3966b71e109f387e871a2e923-194265f6aafvt-X",
    "Content-Type": "application/json"
}

dynamic_vaccount_ref = {}

@app.route('/purchase-airtime', methods=["POST"])
def purchase_airtime():
    data = request.get_json()
    try:
        userId = data["userId"]
        provider = data["provider"]
        number = data["number"]
        amount = float(data["amount"])
        airtime_type = data["airtime_type"]
        print(provider, number, amount, airtime_type)
        trnx_id = "trnx_" + str(int(datetime.utcnow().timestamp()))
        payload = {
            "network": provider["network_id"],
            "phone": number,
            "plan_type": airtime_type,
            "amount": amount,
            "bypass": False,
            "request-id": trnx_id
        }

        userRef = db.collection('users').document(userId)
        user_data = userRef.get().to_dict()
        fcm_token = user_data["fcm_token"] # type: ignore
        if not user_data:
            return jsonify({"status": "fail", "message": "User not found"})
        print("pass1")
        w_bal = float(user_data['wallet_bal'])
        print("pass2")
        
        transaction_data = {
            'user_id': userId,
            "type": "airtime",
            'amount': amount,
            'network': provider["network"],
            'number': number,
            'status': 'pending',
            'trnxId': trnx_id,
            'timestamp': firestore.firestore.SERVER_TIMESTAMP
        }

        if amount <= w_bal:
            print("pass3")
            url = "https://n3tdata.com/api/topup/"
            response = requests.post(url, headers=headers, json=payload)
            
            status_code = response.status_code
            print("Eror not knowing")
            resp_json = response.json()
            print(response.json())
            print("pass4",status_code)
            if status_code in [200, 201]:
                if resp_json["status"] == "success":
                    discount = db.collection('airtime_discount').document("discount").get().to_dict()
                    discount_amount = float(discount["percentage"]) # type: ignore
                    amount = amount - (amount * (discount_amount / 100))
                    userRef.update({'wallet_bal': str(float(w_bal - amount))})
                    print("pass5")
                    total = float(w_bal - amount)
                    transaction_data["balance"] = total
                    transaction_data["status"] = resp_json["status"]
                    
                    db.collection('transactions').document(trnx_id).set(transaction_data)
                    title="Airtime Purchase",
                    body=f"You have successfully purchase N{amount} airtime to {number}"
                    message = messaging.Message(
                        data={
                            "userId": str(userId),
                            "title": str(title),
                            "content": str(body)
                        },
                        token=fcm_token
                    )
                    response = messaging.send(message)
                    print("pass6")
                    return jsonify(resp_json)
                transaction_data["status"] = "fail"
                db.collection('transactions').document(trnx_id).set(transaction_data)
                return jsonify(resp_json)
            elif status_code == 400:
                transaction_data["status"] = "fail"
                db.collection('transactions').document(trnx_id).set(transaction_data)
                return jsonify(resp_json)
            else:
                transaction_data["status"] = resp_json["status"]
                db.collection('transactions').document(trnx_id).set(transaction_data)
                return jsonify({"status": "fail", "message": "Sorry for the inconvenient, try again later!"})
        else:
            return jsonify({"status": "Insufficient balance", "message": "Insufficient balance"})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"status": "fail", "message": str(e)})

@app.route('/purchase-data', methods=["POST"])
def purchase_data():
    data = request.get_json()
    try:
        userId = data["userId"]
        number = data["number"]
        plan = data["plan"]
        amount = float(plan["price"])
        trnx_id = "trnx_" + str(int(datetime.utcnow().timestamp()))

        payload = {
            "network": int(plan["network"]),
            "phone": number,
            "data_plan": int(plan['plan_id']),
            "bypass": False,
            "request-id": trnx_id
        }

        userRef = db.collection('users').document(userId)
        user_data = userRef.get().to_dict()
        
        if not user_data:
            return jsonify({"status": "fail", "message": "User not found"})
        fcm_token = user_data["fcm_token"]
        w_bal = float(user_data["wallet_bal"])
        

        transaction_data = {
            'user_id': userId,
            "type": "data",
            'amount': amount,
            'network': plan['provider'],
            'plan': f"{plan['plan']} - {plan['validate']}",
            'number': number,
            'status': 'pending',
            'trnxId': trnx_id,
            'timestamp': firestore.firestore.SERVER_TIMESTAMP
        }

        if amount <= w_bal:
            url = "https://n3tdata.com/api/data"
            response = requests.post(url, headers=headers, json=payload)
            status_code = response.status_code
            resp_json = response.json()
            print(response.json())
            if status_code in [200, 201]:
                if resp_json["status"] == "success":
                    userRef.update({'wallet_bal': str(float(w_bal - amount))})
                    total = float(w_bal - amount)
                    transaction_data["balance"] = total
                    transaction_data["status"] = resp_json["status"]
                    db.collection('transactions').document(trnx_id).set(transaction_data)
                    title="Data Purchase",
                    body=f"The purchase of {plan['validate']} - N{amount} data to {number} was successful"
                    message = messaging.Message(
                        data={
                            "userId": str(userId),
                            "title": str(title),
                            "content": str(body)
                        },
                        token=fcm_token
                    )
                    response = messaging.send(message)
                    return jsonify(resp_json)
                transaction_data["status"] = resp_json["status"]
                db.collection('transactions').document(trnx_id).set(transaction_data)
                return jsonify(resp_json)
            elif status_code == 400:
                transaction_data["status"] = resp_json["status"]
                db.collection('transactions').document(trnx_id).set(transaction_data)
                return jsonify(resp_json)
            else:
                transaction_data["status"] = resp_json["status"]
                db.collection('transactions').document(trnx_id).set(transaction_data)
                return jsonify({"status": "fail", "message": "Sorry for the inconvenient, try again later"})
        else:
            return jsonify({"status": "Insufficient balance", "message": "Insufficient balance"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})

@app.route('/purchase-cable', methods=["POST"])
def purchase_cable():
    data = request.get_json()
    try:
        userId = data["userId"]
        plan = data["plan"]
        iuc_number = int(data["iuc_number"])
        number = data["number"]
        amount = float(plan["price"])
        trnx_id = "trnx_" + str(int(datetime.utcnow().timestamp()))

        payload = {
            "cable": int(plan["cable_id"]),
            "cable_plan": int(plan['plan_id']),
            "iuc": iuc_number,
            "bypass": False,
            "request-id": trnx_id
        }

        userRef = db.collection('users').document(userId)
        user_data = userRef.get().to_dict()
        
        if not user_data:
            return jsonify({"status": "fail", "message": "User not found"})

        w_bal = float(user_data["wallet_bal"])
        transaction_data = {
            'user_id': userId,
            "type": "cable",
            'amount': amount,
            'network': plan["provider"],
            'plan': plan["plan_name"],
            'iuc_number': iuc_number,
            'number': number,
            'status': 'pending',
            'trnxId': trnx_id,
            'timestamp': firestore.firestore.SERVER_TIMESTAMP
        }

        if amount <= w_bal:
            url = "https://n3tdata.com/api/cable"
            response = requests.post(url, headers=headers, json=payload)
            status_code = response.status_code
            resp_json = response.json()

            if status_code in [200, 201]:
                if resp_json["status"] == "success":
                    userRef.update({'wallet_bal': str(float(w_bal - amount))})
                    total = float(w_bal - amount)
                    transaction_data["balance"] = total
                    transaction_data["status"] = resp_json["status"]
                    db.collection('transactions').document(trnx_id).set(transaction_data)
                    fcm_token = user_data["fcm_token"]

                    title="Cable Subscription Purchase",
                    body=f"The purchase of {plan['plan_name']} - N{amount} was successful"
                    message = messaging.Message(
                        data={
                            "userId": str(userId),
                            "title": str(title),
                            "content": str(body)
                        },
                        token=fcm_token
                    )
                    response = messaging.send(message)
                    return jsonify(resp_json)
                transaction_data["status"] = "fail"
                db.collection('transactions').document(trnx_id).set(transaction_data)
                #error = resp_json.get("error", ["Unknown error"])[0]
                return jsonify({"status": "fail", "message": resp_json["message"]})
            elif status_code == 400:
                transaction_data["status"] = "fail"
                db.collection('transactions').document(trnx_id).set(transaction_data)
                #error = resp_json.get("error", ["Unknown error"])[0]
                return jsonify({"status": "fail", "message": resp_json["message"]})
            else:
                transaction_data["status"] = resp_json["status"]
                db.collection('transactions').document(trnx_id).set(transaction_data)
                return jsonify({"status": "fail", "message": "Sorry for the inconvenient, try again later"})
        else:
            return jsonify({"status": "Insufficient balance", "message": "Insufficient balance"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})

@app.route('/purchase-electricity', methods=["POST"])
def purchase_electricity():
    data = request.get_json()
    try:
        userId = data["userId"]
        disco = str(data["disco_id"])
        amount = float(data["amount"])
        meter_number = int(data["meter_number"])
        number = data["number"]
        meter_type = str(data["meter_type"])
        trnx_id = "trnx_" + str(int(datetime.utcnow().timestamp()))

        payload = {
            "disco": int(disco),
            "amount": amount,
            "meter_number": meter_number,
            "meter_type": meter_type,
            "bypass": False,
            "request-id": trnx_id
        }

        userRef = db.collection('users').document(userId)
        user_data = userRef.get().to_dict()
        if not user_data:
            return jsonify({"status": "fail", "message": "User not found"})

        w_bal = float(user_data["wallet_bal"])
        transaction_data = {
            'user_id': userId,
            "type": "electricity",
            'amount': amount,
            'network': None,
            'meter_number': meter_number,
            'meter_type': meter_type,
            'number': number,
            'units': None,
            'status': 'pending',
            'trnxId': trnx_id,
            'timestamp': firestore.firestore.SERVER_TIMESTAMP
        }

        if amount <= w_bal:
            url = "https://n3tdata.com/api/bill"
            response = requests.post(url, headers=headers, json=payload)
            status_code = response.status_code
            resp_json = response.json()

            if status_code in [200, 201]:
                if resp_json["status"] == "success":
                    userRef.update({'wallet_bal': str(float(w_bal - amount))})
                    total = float(w_bal - amount)
                    transaction_data["balance"] = total
                    transaction_data["status"] = resp_json["status"]
                    transaction_data["units"] = resp_json["token"]
                    disco_name = resp_json["disco_name"]
                    transaction_data["network"] = disco_name
                    db.collection('transactions').document(trnx_id).set(transaction_data)
                    fcm_token = user_data["fcm_token"]

                    title="Electric Bill Purchase",
                    body=f"The purchase of N{amount} {disco_name} Electric bill was successful."
                    message = messaging.Message(
                        data={
                            "userId": str(userId),
                            "title": str(title),
                            "content": str(body)
                        },
                        token=fcm_token
                    )
                    response = messaging.send(message)
                    return jsonify(resp_json)
                print(resp_json)
                transaction_data["status"] = "fail"
                db.collection('transactions').document(trnx_id).set(transaction_data)
                return jsonify(resp_json)
            elif status_code == 400:
                print(resp_json)
                transaction_data["status"] = "fail"
                db.collection('transactions').document(trnx_id).set(transaction_data)
                return jsonify(resp_json)
            else:
                transaction_data["status"] = "pending"
                db.collection('transactions').document(trnx_id).set(transaction_data)
                return jsonify({"status": "pending", "message": "Sorry for the inconvenient, try again later."})
        else:
            return jsonify({"status": "Insufficient balance", "message": "Insufficient balance"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})

@app.route('/purchase-edupin', methods=["POST"])
def purchase_edupin():
    data = request.get_json()
    try:
        userId = data["userId"]
        exam = str(data["exam"])
        exam_id = int(data["exam_id"])
        quantity = float(data["quantity"])
        amount = float(data["amount"])
        number = data["number"]
        trnx_id = "trnx_" + str(int(datetime.utcnow().timestamp()))

        payload = {
            "exam": exam_id,
            "quantity": quantity,
        }

        userRef = db.collection('users').document(userId)
        user_data = userRef.get().to_dict()
        if not user_data:
            return jsonify({"status": "fail", "message": "User not found"})

        w_bal = float(user_data["wallet_bal"])
        transaction_data = {
            'user_id': userId,
            "type": "Education",
            "quantity": quantity,
            'amount': amount,
            'network': exam,
            'meter_number': None,
            'meter_type': None,
            'number': number,
            'pins': None,
            'units': None,
            'status': 'pending',
            'trnxId': trnx_id,
            'timestamp': firestore.firestore.SERVER_TIMESTAMP
        }

        if amount <= w_bal:
            url = "https://n3tdata.com/api/exam"
            response = requests.post(url, headers=headers, json=payload)
            status_code = response.status_code
            resp_json = response.json()

            if status_code in [200, 201]:
                if resp_json["status"] == "success":
                    userRef.update({'wallet_bal': str(float(w_bal - amount))})
                    total = float(w_bal - amount)
                    transaction_data["balance"] = total
                    transaction_data["status"] = resp_json["status"]
                    transaction_data["pins"] = resp_json["pin"]
                    db.collection('transactions').document(trnx_id).set(transaction_data)
                    fcm_token = user_data["fcm_token"]
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title="Electric Bill Purchase",
                            body=f"The purchase of {exam} was successful."
                        ),
                        data={
                            "userId": userId
                        },
                        token=fcm_token
                    )
                    response = messaging.send(message)
                    return jsonify(resp_json)
                print(resp_json)
                transaction_data["status"] = resp_json["status"]
                db.collection('transactions').document(trnx_id).set(transaction_data)
                return jsonify(resp_json)
            elif status_code == 400:
                print(resp_json)
                transaction_data["status"] = resp_json["status"]
                db.collection('transactions').document(trnx_id).set(transaction_data)
                return jsonify(resp_json)
            else:
                transaction_data["status"] = "fail"
                db.collection('transactions').document(trnx_id).set(transaction_data)
                return jsonify({"status": "pending", "message": "Sorry for the inconvenient, try again later."})
        else:
            return jsonify({"status": "Insufficient balance", "message": "Insufficient balance"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})

# @app.route('/transaction-webhook', methods=["POST"]) # type: ignore
# def retry_failed_transaction():
#     data = request.get_json()
#     trnxId = data["request-id"]
#     transaction = db.collection('transactions').document(trnxId).get().to_dict()
#     if not transaction:
#         return jsonify({"status": "fail", "message": "Transaction not found"})
#     if transaction["status"] == "pending":
#         if data["status"] == "success":
#             db.collection('transactions').document(trnxId).update({"status": "success"})
#             print({"status": "success", "message": "Transaction updated to success"})
#     return jsonify({"status": "success", "message": "Transaction updated to success"})
        
        

@app.route('/verify-meter-number', methods=["POST"])
def verify_meter_number():
    data = request.get_json()
    try:
        disco = int(data["disco"])
        meter_number = str(data["meter_number"])
        meter_type = str(data["meter_type"])
        
        url = f"https://n3tdata.com/api/bill/bill-validation?meter_number={meter_number}&disco={disco}&meter_type={meter_type}"
        response = requests.get(url, headers=headers)
        status_code = response.status_code
        resp_json = response.json()

        if status_code in [200, 201]:
            if resp_json["status"] == "success":
                return jsonify(resp_json)
            else:
                return jsonify({"status": "fail", "message": "Sorry for the inconvenient, try again later."})
        elif status_code == 400:
            return jsonify(resp_json)
        else:
            return jsonify({"status": "fail", "message": "Sorry for the inconvenient, try again later."})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})

@app.route('/verify-iucnumber', methods=["POST"])
def verify_iucnumber():
    data = request.get_json()
    try:
        iuc_number = str(data["iuc_number"])
        cable = str(data["cable_id"])
        
        url = f"https://n3tdata.com/api/cable/cable-validation?iuc={iuc_number}&cable={cable}"
        response = requests.get(url, headers=headers)
        status_code = response.status_code
        resp_json = response.json()

        if status_code in [200, 201]:
            if resp_json["status"] == "success":
                return jsonify(resp_json)
            else:
                return jsonify({"status": "fail", "message": "Sorry for the inconvenient, try again later."})
        elif status_code == 400:
            return jsonify(resp_json)
        else:
            return jsonify({"status": "fail", "message": "Sorry for the inconvenient, try again later."})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})

@app.route('/verify-bvn', methods=["POST"])
def verify_bvn():
    data = request.get_json()
    bvn = data["bvn"]
    userId = data["userId"]
    query = db.collection('users').where('bvn', "==", bvn).get()
    print(len(query))
    if len(query)>0:
        return jsonify({"status": "fail", "message": "This BVN is already been used by another user!"})
    userRef = db.collection('users').document(userId)
    userRef.update({"bvn": bvn})
    return jsonify({"status": "success", "message": "BVN successfully verified"})

@app.route('/create-virtual-account', methods=["POST"]) # type: ignore
def create_virtual_account():
    data = request.get_json()
    userId = data["userId"]
    userRef = db.collection('users').document(userId)
    user_data = userRef.get().to_dict()
    try:
        bvn = data["bvn"]
        amount = 0.0
        if data["amount"] != "":
            amount = float(data["amount"])
        tx_ref = f"tx_ref_{userId}_{int(datetime.utcnow().timestamp())}"
        fullname = user_data['name'].split(" ") # type: ignore
        firstName = ""
        lastName = ""
        if len(fullname) > 1:
            firstName = fullname[0]
            lastName = fullname[1]
        else:
            firstName = fullname[0]
            lastName = fullname[0]
        payload = {
            "email":user_data['email'], # type: ignore
            "tx_ref": tx_ref,
            "phonenumber":user_data["phone"], # type: ignore
            "firstname":firstName, # type: ignore
            "lastname":lastName, # type: ignore
            
        }
        account_name = f"{userId} FLW"
        if bvn != "":
            print("bvn provided")
            payload["is_permanent"] = True
            payload["bvn"] = bvn
            payload["narration"]=userId
        else:
            print("bvn not provided")
            dynamic_vaccount_ref[tx_ref] = userId
            payload["amount"] = amount
            payload["narration"]=userId
            print(dynamic_vaccount_ref)

        url = "https://api.flutterwave.com/v3/virtual-account-numbers"
        response = requests.post(url, headers=headers2, json=payload)
        status_code = response.status_code
        resp_json = response.json()
        print(resp_json)
        if status_code in [200, 201]:
            if resp_json["status"] == "success":
                virtual_account = resp_json["data"]
                virtual_account["account_name"] = account_name
                if bvn != "":
                    db.collection("virtualAccounts").document(tx_ref).set({"userId":userId, "virtualAccount":virtual_account})
                return jsonify({"status": "success", "message": virtual_account})
        elif status_code == 400:
            return jsonify({"status": "fail", "message": resp_json, "code":status_code})
        else:
            return jsonify({"status": "pending", "message": resp_json, "code":status_code})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"status": "fail", "message": str(e), "code":"None"})

@app.route('/funding-webhook', methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        event = data["event"]
        status = data["data"]["status"]
        flw_ref = data["data"]["flw_ref"]
        tx_ref = data["data"]["tx_ref"]
        email = data["data"]["customer"]["email"]
        # date_created = data["data"]["created_datetime"]
        userId = None
        if tx_ref in dynamic_vaccount_ref:
            userId = dynamic_vaccount_ref[tx_ref]
            print(dynamic_vaccount_ref)
            del dynamic_vaccount_ref[tx_ref]
            print(dynamic_vaccount_ref)
        else:
            virtualAccount = db.collection('virtualAccounts').document(tx_ref).get().to_dict()
            if virtualAccount is not None:
                userId = virtualAccount["userId"]
            else:
                return jsonify({"status":"fail"})
        
        userData = db.collection("users").document(userId).get().to_dict()
        charges = db.collection("transferCharges").document("charges").get().to_dict()
        amount = float(data["data"]["amount"]) # type: ignore
        body = ""
        #Device token
        title = "Wallet Funding"
        if status == "successful":
            total = float(userData['wallet_bal']) + (amount - float(charges["amount"])) # type: ignore
            print(amount,total)
            db.collection('users').document(userId).update({"wallet_bal":str(total)})
            wallet_fundings = {
                "userId": userId,
                "balance_before": str(float(userData['wallet_bal'])), # type: ignore
                "amount_credited": str(amount),
                "charges": str(float(charges["amount"])), # type: ignore
                "balance_after": str(total),
                "created_at": firestore.firestore.SERVER_TIMESTAMP,
                "tx_ref": tx_ref,
                "timestamp": firestore.firestore.SERVER_TIMESTAMP
            }
            db.collection('walletFundings').document().set(wallet_fundings)
            body = f"Your wallet has been successfully credited with the sum of ₦{amount}. Please note that a ₦{charges["amount"]} service fee was deducted as part of the transaction." # type: ignore
        else:
            body = f"The transfer of ₦{amount} was not successful, please try again later to avoid double transaction"
        
        fcm_token = userData["fcm_token"] # type: ignore
        notification = {
            "id": userId,
            "title": title,
            "content":body,
            'timestamp': firestore.firestore.SERVER_TIMESTAMP
        }
        db.collection('notifications').document().set(notification)
        message = messaging.Message(
            data={
                "userId": userId,
                "title": title,
                "content": body
            },
            token=fcm_token
        )
        response = messaging.send(message)
        return jsonify({"status": "success", "message_id": response,"token":fcm_token})
    except Exception as e:
        return jsonify({"status": "fail", "error": str(e)}) # type: ignore

@app.route('/send-notification', methods=["POST"])
def send_notification():
    data = request.get_json()
    users = data["users"]
    msg = data["message"]
    title = data["title"]
    successful = []
    failed = []
    for user in users:
        print(user)
        notification = {
            "id": user["id"],
            "title": title,
            "content": msg,
            'timestamp': firestore.firestore.SERVER_TIMESTAMP
        }
        db.collection('notifications').document().set(notification)
        userData = db.collection('users').document(user["id"]).get().to_dict()
        try:
            message = messaging.Message(
                data={
                    "userId": user["id"],
                    "title": title,
                    "content": msg
                },
                token=userData["fcm_token"] # type: ignore
            )
            response = messaging.send(message)
            successful.append(user)
        except Exception as e:
            failed.append({"data": user, "error": str(e)})
    return jsonify({"status": "success", "successful": successful, "failed": failed})

@app.route('/delete-users', methods=["POST"])
def delete_users():
    data = request.get_json()
    users = data["users"]
    uids = []
    page = auth.list_users()
    successful = []
    failed = []
    while page:
        for user in page.users:
            print(f"UID: {user.uid}, Email: {user.email}")
            id = user.email.split("@")[0]
            for user_data in users:
                if user_data["id"] == id:
                    print(f"Deleting user: {user.uid}")
                    try:
                        auth.delete_user(user.uid)
                        successful.append(id)
                    except Exception as e:
                        print(f"Error deleting user {user.uid}: {str(e)}")
                        failed.append({"uid": id, "error": str(e)})
                    break
            uids.append(user.uid)

        # Go to next page if available
        page = page.get_next_page()
    return jsonify({"status": "success", "deleted_users": uids})

@app.route('/keep-quiktopp-server-alive', methods=["POST", "GET"])
def keep_quiktopp_server_alive():
    # This endpoint is used to keep the server alive
    return jsonify({"status": "success", "message": "Server is alive!"})

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0', port=80)
