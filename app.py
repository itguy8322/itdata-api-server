import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import firebase_admin
from firebase_admin import credentials, auth, firestore
import os


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
    
    userId = request.form["userId"]
    network = int(request.form["network"])
    number = request.form["number"]
    amount = request.form["amount"],
    airtime_type = request.form["airtime_type"]
    amount = amount[0]
    payload = {
        "network": network,
        "mobile_number": number,
        "airtime_type": airtime_type,
        "amount": amount,
        "Ported_number": False
    }

    w_bal = 1550

    print("wallet_balance: ",w_bal," amount: ",amount)
    if int(amount) <= w_bal:
        print("balance sufficient")
        total = float(w_bal) - float(amount)
        print("Total: ", total)
        try:
            url = "https://postranet.com/api/topup/"
            response = requests.post(url, headers=headers, json=payload)
            print(response.status_code)
            print(response.json())
            d = response.json()
            if response.status_code == 200 or response.status_code == 201:
                return jsonify({"status":"success", "wallet_bal": f"{total}"})
            elif response.status_code == 400:
                total = total + float(amount)
                print("Total: ", total)
                error = response.json()['error'][0]
                if "Please check," in error:
                    return jsonify({"status": error, "wallet_bal": f"{total}"})
                else:
                    userData = db.collection('users').document(userId).get().to_dict()
                    return jsonify({"status":"Sorry for the inconvenient, Please try again later!", "wallet_bal": f"{total}", "userData": userData})
            else:
                return jsonify({"status":"pending", "data": response.json(), "wallet_bal": f"{total}", "transactions":[]})
        except Exception as e:
            total = total + float(amount)
            print("Total: ", total)

            return jsonify({"status":"fail","message":f"{e}", "wallet_bal": f"{total}", "transactions":[]})
    else:
        print("balance insufficient")
        return jsonify({"status":"Insufficient balance"})

@app.route('/purchase-data')
def purchase_data():
    
    userId = request.form["userId"]
    network = int(request.form["network"])
    number = request.form["number"]
    planId = request.form["planId"]
    amount = request.form["amount"],
    amount = float(request.form["cost"])
    w_bal = 1550
    print("wallet_balance: ",w_bal," amount: ",amount)
    if float(amount) <= w_bal:
        print("balance sufficient")
        total = w_bal - amount
        print("Total: ", total)

        number = request.form["number"]
        payload = {
            "network": network,
            "mobile_number": number,
            "plan": planId,
            "Ported_number": False
        }
        
        try:
            url = "https://postranet.com/api/data/"
            response = requests.post(url, headers=headers, json=payload)
            print(response.status_code)
            print(response.json())
            d = response.json()
            if response.status_code == 200 or response.status_code==201:
                return jsonify({"status":"success", "wallet_bal": f"{total}", "transactions":[]})
            elif response.status_code == 400:
                total = total + float(amount)
                print("Total: ", total)
                error = response.json()['error'][0]
                if "Please check," in error:
                    return jsonify({"status": error, "wallet_bal": f"{total}"})
                else:
                    return jsonify({"status":"Unexpected errror has occured. Please try again later.","wallet_bal": f"{total}"})
            else:
                return jsonify({"status":"pending", "data": response.json(), "wallet_bal": f"{total}", "transactions":[]})
        except Exception as e:
            print(f"ERROR22: {e}")
            total = total + float(amount)
            print("Total: ", total)
            return jsonify({"status":"fail", "wallet_bal": f"{total}", "transactions":[]})
    else:
        print("balance insufficient")
        return jsonify({"status":"Insufficient balance"})

@app.route('/purchase-cable')
def purchase_cable():
    cable_userId = int(request.form["cable_userId"])
    cableplan = request.form["cableplan"]
    card_number = request.form["card_number"]
    payload = {
        "cable_userId": cable_userId,
        "cableplan": cableplan,
        "smart_card_number": card_number
    }
    url = "https://postranet.com/api/cablesub/"
    response = requests.post(url, headers=headers, json=payload)
    print(response.status_code)
    if response.status_code == 200:
        return jsonify({"status":"ok", "data": response.json(), "wallet_bal": f"{1550}"})
    else:
        return jsonify({"status":"Error", "data": response.json()})

@app.route('/purchase-edupin')
def purchase_edupin():
    pass

@app.route('/purchase-electricity')
def purchase_electricity():
    disco_name = int(request.form["disco_name"])
    amount = request.form["amount"]
    meter_number = request.form["meter_number"]
    meter_type = int(request.form["meter_type"])
    payload = {
        "disco_name": disco_name,
        "amount": amount,
        "meter_number": meter_number,
        "MeterType": meter_type
    }
    url = "https://postranet.com/api/billpayment/"
    response = requests.post(url, headers=headers, json=payload)
    print(response.status_code)
    if response.status_code == 200:
        return jsonify({"status":"ok", "data": response.json(), "wallet_bal": f"{1550}"})
    else:
        return jsonify({"status":"Error", "data": response.json()})

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0', port=80)
