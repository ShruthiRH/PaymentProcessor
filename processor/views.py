from datetime import datetime
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
import requests
from .utils import generate_transcript_id

'''
1. Backend -> PP record when it got this request
2. PP -> Bank for User check record and note down the reply
3. PP -> Bank for NGO check record and note down the reply
4. PP -> Transfer Money record amount, date time, accounts and the reply
5. PP -> Backend -> sends the transcript with it
6. PP generates random id for every transaction 

'''

@csrf_exempt
@api_view(['POST'])
def initiate_payment(request):

    #Make notes on everything happing in the transaction
    transcript = {}

    transcript['Process Initiation'] = {
        'Transaction ID' : generate_transcript_id(),
        'time': str(datetime.now())
    }

    bank_response_for_ngo = {}
    bank_response_for_payment = {}
    bank_response_for_user = {}

    data = json.loads(request.body)
    print("Hello! Here")
    card_number = data.get('card_number')
    cvv = data.get('cvv')
    expiry_date = data.get('expiry_date')
    name = data.get('name')
    amount = data.get('amount')
    ngo_account_number = data.get('ngo_account_number')


    #check if sender has valid account and has money

    try:

        transcript['Checking User Verification'] = {
            'card_number': card_number,
            'amount': amount,
            'name' : name,
            'time': str(datetime.now())
        }

        bank_response_for_user = requests.post(
            "http://localhost:3000/api/bank/check-user/",
            json={
                'card_number': card_number,
                'cvv': cvv,
                'amount': amount,
                'name' : name,
                'expiry_date': expiry_date
            },
            timeout=10  # Set a timeout for the request
        )

        transcript['Bank Response for User Verification'] = bank_response_for_user.json()
        print(bank_response_for_user.status_code)

        if bank_response_for_user.status_code == 200:

            #continue checking for ngo and make transaction
            transcript['Checking NGO Verification'] = {
                'account_number':ngo_account_number,
                'time': str(datetime.now())
            }

            bank_response_for_ngo = requests.post(
                "http://localhost:3000/api/bank/check-ngo/",
                json={
                    'account_number':ngo_account_number
                },
                timeout=10  # Set a timeout for the request
            )

            transcript['Bank Response for NGO Verification'] = bank_response_for_ngo.json()

            if bank_response_for_ngo.status_code == 200:
                #go ahead and make the transaction!

                transcript['Making Money Transfer'] = {
                    'time': str(datetime.now())
                }

                bank_response_for_payment = requests.post(
                    "http://localhost:3000/api/bank/make-transaction/",
                    json={
                        'ngo_account_number':ngo_account_number,
                        'card_number': card_number,
                        'cvv': cvv,
                        'amount': amount,
                        'user_name' : name,
                        'expiry_date': expiry_date
                    },
                    timeout=10  # Set a timeout for the request
                )

                transcript['Bank Response for Money Transfer'] = bank_response_for_payment.json()

                if bank_response_for_payment.status_code == 200:
                    return JsonResponse(
                        {
                            'message': 'Payment successful! Money Transfered safely!',
                            'details': bank_response_for_payment.json(),
                            'transcript': transcript
                        },
                        status=200
                    )
                else:
                    return JsonResponse(
                        {
                            'message': 'Payment failed! Money was not transfered!',
                            'details': bank_response_for_payment.json(),
                            'transcript': transcript
                        },
                        status=bank_response_for_payment.status_code
                    )
            else:
                return JsonResponse(
                {
                    'message': 'Payment failed! NGO failed verification!',
                    'details': bank_response_for_ngo.json(),
                    'transcript': transcript
                },
                status=bank_response_for_ngo.status_code
            )
        else:
            return JsonResponse(
                {
                    'message': 'Payment failed! User failed verification!',
                    'details': bank_response_for_user.json(),
                    'transcript': transcript
                },
                status=bank_response_for_user.status_code
            )

    except requests.RequestException as e:
        transcript['Error Code'] = str(e)  # Convert the exception to a string
        print(f"Error communicating with the Bank while checking for User: {e}")
        return JsonResponse(
            {
                'message': 'Bank server error',
                'error': str(e),
                'transcript': transcript
            },
            status=500
        )


import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from django.conf import settings


def load_public_key():
    # Read publickeys.json
    with open('publickeys.json', 'r') as f:
        keys_data = json.load(f)
    
    # Choose the public key (keypair_1, keypair_2, etc.)
    public_key_str = keys_data.get("payment processor")
    
    # Load the public key into an object
    public_key = serialization.load_pem_public_key(public_key_str.encode('utf-8'))

    print(public_key)
    return public_key


def encrypt_message(message, public_key):
    # Encrypt the message using RSA and the public key
    encrypted = public_key.encrypt(
        message.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    print(encrypted)
    return encrypted
