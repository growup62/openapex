import os
import sys
import logging

# Add project root to sys.path
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO)
from tools.whatsapp_operator import WhatsAppOperator

print("Testing WhatsApp QR capture...")
result = WhatsAppOperator.show_qr()
print(f"Result: {result}")
