from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

# Generate private key
private_key = ec.generate_private_key(ec.SECP256R1())
private_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Get public key
public_key = private_key.public_key()
public_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)

# Encode to base64
vapid_private_key = base64.urlsafe_b64encode(
    private_key.private_numbers().private_value.to_bytes(32, 'big')
).decode('utf-8')

vapid_public_key = base64.urlsafe_b64encode(public_bytes).decode('utf-8')

print("VAPID_PRIVATE_KEY:", vapid_private_key)
print("VAPID_PUBLIC_KEY:", vapid_public_key)

