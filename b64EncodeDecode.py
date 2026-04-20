import base64

def encode():

    login = "MyLoginName"
    password = "MyPassword"

    credentials = f"{login}:{password}"
    base64_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    print(base64_credentials)


import base64

def decode():
    encoded_data = "TXlMb2dpbk5hbWU6TXlQYXNzd29yZA=="

    decoded_bytes = base64.b64decode(encoded_data)
    decoded_string = decoded_bytes.decode("utf-8")

    # Split back into login and password
    login, password = decoded_string.split(":", 1)

    print("Login:", login)
    print("Password:", password)

print("Encoded Text")
encode()

decode()