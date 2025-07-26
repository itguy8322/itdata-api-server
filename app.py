import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import firebase_admin
from firebase_admin import credentials, auth, firestore, messaging
import os, time
from datetime import datetime


# Load the service account key
cred = credentials.Certificate("/etc/secrets/config.json")
firebase_admin.initialize_app(cred)

# Now you can use Firestore, Auth, etc.
db = firestore.client()


app = Flask(__name__)
CORS(app)
headers = {
    "Authorization": "Token 94af83d1c32ff92892cfa4bfe7f7732f7a4c7925"  # Replace <value> with the actual API key or token.
}
@app.route('/purchase-airtime', methods=["POST"])
def purchase_airtime():
    data = request.get_json()
    try:
        userId = data["userId"]
        network = int(data["network"])
        number = data["number"]
        amount = float(data["amount"])
        airtime_type = data["airtime_type"]

        payload = {
            "network": network,
            "phone": number,
            "plan_type": airtime_type,
            "amount": amount,
            "bypass": False,
            "request-id": f"Airtime_{time.strftime("%d%m%Y%H%M%S")}"
        }

        userRef = db.collection('users').document(userId)
        user_data = userRef.get().to_dict()
        fcm_token = user_data["fcm_token"] # type: ignore
        if not user_data:
            return jsonify({"status": "fail", "message": "User not found"})
        print("pass1")
        w_bal = float(user_data['wallet_bal'])
        trnx_id = "trnx_" + str(int(datetime.utcnow().timestamp()))
        print("pass2")
        transaction_data = {
            'user_id': userId,
            "type": "airtime",
            'amount': amount,
            'network': network,
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
                
                userRef.update({'wallet_bal': float(w_bal - amount)})
                print("pass5")
                total = float(w_bal - amount)
                transaction_data["balance"] = total
                transaction_data["status"] = resp_json["status"]
                
                db.collection('transactions').document(trnx_id).set(transaction_data)
                message = messaging.Message(
                    notification=messaging.Notification(
                        title="Airtime Purchase",
                        body=f"You have successfully purchase N{amount} airtime to {number}"
                    ),
                    data={
                        "userId": userId
                    },
                    token=fcm_token
                )
                response = messaging.send(message)
                print("pass6")
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
            return jsonify({"status": "fail", "message": "Insufficient balance"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})

@app.route('/purchase-data')
def purchase_data():
    data = request.get_json()
    try:
        userId = data["userId"]
        number = data["number"]
        plan = data["plan"]
        amount = float(plan["price"])

        payload = {
            "network": int(plan["network"]),
            "phone": number,
            "data_plan": int(plan['plan_id']),
            "bypass": False,
            "request-id": f"Data_{time.strftime("%d%m%Y%H%M%S")}"
        }

        userRef = db.collection('users').document(userId)
        user_data = userRef.get().to_dict()
        
        if not user_data:
            return jsonify({"status": "fail", "message": "User not found"})
        fcm_token = user_data["fcm_token"]
        w_bal = float(user_data["wallet_bal"])
        trnx_id = "trnx_" + str(int(datetime.utcnow().timestamp()))

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

            if status_code in [200, 201]:
                userRef.update({'wallet_bal': float(w_bal - amount)})
                total = float(w_bal - amount)
                transaction_data["balance"] = total
                transaction_data["status"] = resp_json["status"]
                db.collection('transactions').document(trnx_id).set(transaction_data)
                message = messaging.Message(
                    notification=messaging.Notification(
                        title="Data Purchase",
                        body=f"The purchase of {plan['validate']} - N{amount} data to {number} was successful"
                    ),
                    data={
                        "userId": userId
                    },
                    token=fcm_token
                )
                response = messaging.send(message)
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
            return jsonify({"status": "fail", "message": "Insufficient balance"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})

@app.route('/purchase-cable')
def purchase_cable():
    data = request.get_json()
    try:
        userId = data["userId"]
        plan = data["plan"]
        iuc_number = int(data["iuc_number"])
        number = data["number"]
        amount = float(plan["price"])

        payload = {
            "cable": int(plan["cable_id"]),
            "cable_plan": int(plan['plan_id']),
            "iuc": iuc_number,
            "bypass": False,
            "request-id": f"Cable_{time.strftime("%d%m%Y%H%M%S")}"
        }

        userRef = db.collection('users').document(userId)
        user_data = userRef.get().to_dict()
        
        if not user_data:
            return jsonify({"status": "fail", "message": "User not found"})

        w_bal = float(user_data["wallet_bal"])
        trnx_id = "trnx_" + str(int(datetime.utcnow().timestamp()))
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
                userRef.update({'wallet_bal': float(w_bal - amount)})
                total = float(w_bal - amount)
                transaction_data["balance"] = total
                transaction_data["status"] = resp_json["status"]
                db.collection('transactions').document(trnx_id).set(transaction_data)
                fcm_token = user_data["fcm_token"]
                message = messaging.Message(
                    notification=messaging.Notification(
                        title="Cable Subscription Purchase",
                        body=f"The purchase of {plan['plan_name']} - N{amount} was successful"
                    ),
                    data={
                        "userId": userId
                    },
                    token=fcm_token
                )
                response = messaging.send(message)
                return jsonify(resp_json)
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
            return jsonify({"status": "fail", "message": "Insufficient balance"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})

@app.route('/purchase-electricity')
def purchase_electricity():
    data = request.get_json()
    try:
        userId = data["userId"]
        disco = str(data["disco_id"])
        amount = float(data["amount"])
        meter_number = int(data["meter_number"])
        number = data["number"]
        meter_type = str(data["meter_type"])

        payload = {
            "disco": int(disco),
            "amount": amount,
            "meter_number": meter_number,
            "meter_type": meter_type,
            "bypass": False,
            "request-id": f"Bill_{time.strftime("%d%m%Y%H%M%S")}"
        }

        userRef = db.collection('users').document(userId)
        user_data = userRef.get().to_dict()
        if not user_data:
            return jsonify({"status": "fail", "message": "User not found"})

        w_bal = float(user_data["wallet_bal"])
        trnx_id = "trnx_" + str(int(datetime.utcnow().timestamp()))
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
                userRef.update({'wallet_bal': float(w_bal - amount)})
                total = float(w_bal - amount)
                transaction_data["balance"] = total
                transaction_data["status"] = resp_json["status"]
                transaction_data["units"] = resp_json["token"]
                disco_name = resp_json["disco_name"]
                transaction_data["network"] = disco_name
                db.collection('transactions').document(trnx_id).set(transaction_data)
                fcm_token = user_data["fcm_token"]
                message = messaging.Message(
                    notification=messaging.Notification(
                        title="Electric Bill Purchase",
                        body=f"The purchase of N{amount} {disco_name} Electric bill was successful."
                    ),
                    data={
                        "userId": userId
                    },
                    token=fcm_token
                )
                response = messaging.send(message)
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
            return jsonify({"status": "fail", "message": "Insufficient balance"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})

@app.route('/purchase-edupin')
def purchase_edupin():
    data = request.get_json()
    try:
        userId = data["userId"]
        exam = str(data["exam"])
        exam_id = int(data["exam_id"])
        quantity = float(data["quantity"])
        amount = float(data["amount"])
        number = data["number"]

        payload = {
            "exam": exam_id,
            "quantity": quantity,
            "request-id": f"Exam_{time.strftime("%d%m%Y%H%M%S")}"
        }

        userRef = db.collection('users').document(userId)
        user_data = userRef.get().to_dict()
        if not user_data:
            return jsonify({"status": "fail", "message": "User not found"})

        w_bal = float(user_data["wallet_bal"])
        trnx_id = "trnx_" + str(int(datetime.utcnow().timestamp()))
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
                userRef.update({'wallet_bal': float(w_bal - amount)})
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
            return jsonify({"status": "fail", "message": "Insufficient balance"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0', port=80)
