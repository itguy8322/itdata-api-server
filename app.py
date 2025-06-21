from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import firebase_admin
from firebase_admin import credentials, auth, firestore

# Load the service account key
cred = credentials.Certificate({
  "type": "service_account",
  "project_id": "it-project-83335",
  "private_key_id": "1a969fd9efc534c8713e7c7cc814eec8ab5fddc1",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDA4Nm5BWoBl/b2\nD2sZyZjbr4fptwyviqwKepHzquMk8OieoefHdOYUPCIb+/uBWNFbdRr8dgfKuV3P\neG3TMLI2+S1mfScccymFBAKurFhmDOKo57W8QWpVvMPzkCEz3hETJzt/tGgZ5oX7\nHyKglhBfro3VTt2zJwqK+m8yrBK7lLX7yC+3mUbqyusNwiy0QRCXlKFVKcSdmfY8\n75eUKxeQ4I8NjBwDrSU1mC0wers/rZBuwSVdUutoAq6xUBVaM49zKaKhbwuh7LxX\njkMkWpmkyuxHC+7yfI4dQWWP6kQN7tTykW9x8KtA8XQJXZphC0qKNCB7niZcyROU\nHCS2vfHHAgMBAAECggEAW5xwzUidCRS84DKClEUErZO54nBnPhmHjZKaMDpCmREz\n6+TKyhnkDkhhixksZEtjZSVCJBeLq+ZPgHOa9mxyuVmxDrTzFrg8SEmXXI/PjOkh\n30fvMfOAJij6iX0zyAb55TcFM6rkpyivCo/HSq78J/Yot+A1vRoWD9zTZCYG38D3\nduDhtggrHgau/8ikI9V6wCHOPS4sC8zPamZ3EDq8U2q2fqxJnVNEGEvdQoRrA/Jg\nzCBQ12bDygNZTwR++cYPpHOnFZ/tjJd1hvJVW4Vy2pjDmkatRANlivWR2xm1h33p\nLrZ1hf39V0gaCakjDofbfs4brIQlGARPHd9UnlQWwQKBgQDgAhENt3Xr7W9eBduV\n3Ag3YKlbsxljzolqYL/MYq0OQE0F4K8G+nPTN4tCLxdWnjVGtM+8Tz/XJGl4XfiF\nWu+BUw1Uk5A2DdCGxoiWURtWUKmz7qdcpNhWdHDeElP8eHpcFzSf/cFrXWwJ2bwI\n8m35OstvZt7TW9B5RgE0IcpKqwKBgQDcbKcTExIsjgVz2EUJFwp55nuRsqxc6S1n\nJ3idR9jb3fkaspj79KgJuPfiZl3SLD+Z8KxrKaUc8TugoJnVGAdAPSn18nFlCR1P\nb6qVF3OEEYSELfAOXdIxnrkAaY6CyZm0jwu3/rcmcwlRkKZEMaqXUyVdgKYtmWbQ\nGxAQP1l1VQKBgA1vskwrU/Rp0oNGQKyVfRytPJtWe9BjxBRQZ1DAHnc7XiNbHcSC\nY04pB75ZisHUTYfHMqqt6jtiYL0qjcyZ7sHIFIWdMEo9u+NJp0m05bngrr0vNHS3\nIo7U/ywi10zOgTBi5/Isy1xAR0mz+LZkrDoFz8wH1JfC6xdLHqlc2YBvAoGATpaW\nguB7zFLecs0a4ADNBWU9jVbMyVuBipOyFzF0if98Px6KGNrDxqOiDaA9tx97laEP\neC2i5szDW6Om9SjZ/PdRrJTCBSnYv2eqw/lWgDHWs2HFgvnEZViX0SPRYaQLHysZ\nHIK+PgEpw2D1Rr8GeWl1mv6xQPS+iVf8xC4x8PkCgYBYmJY5qNvvwO140thH4AYT\nRws3hCvnJRYupRZ3Ec3j93/v3cvDR4gGx+1m64PrTQI+WqJgQK2SRLZQTvFfOTN6\nv+R+cca4+WmcwjWvC2e81XhloC+hGmGEYoSsNFoXCBfwXO7LGQ1kFxzWRUVngnPB\nVzeJC3iOr9Gc08ZYxYaC6g==\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@it-project-83335.iam.gserviceaccount.com",
  "client_id": "108831822163714957496",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40it-project-83335.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
})
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
