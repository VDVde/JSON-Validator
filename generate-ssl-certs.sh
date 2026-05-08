#!/bin/bash
# generate-ssl-certs.sh
# Generates self-signed SSL certificates for development/testing

set -e

SSL_DIR="nginx/ssl"
DAYS=365
COUNTRY="DE"
STATE="Germany"
CITY="Berlin"
ORG="VDV463 Validator"
COMMON_NAME="${1:-localhost}"

echo "🔐 Generating SSL certificates for: $COMMON_NAME"

# Create SSL directory if it doesn't exist
mkdir -p "$SSL_DIR"

# Generate private key and certificate
openssl req -x509 -nodes \
    -days $DAYS \
    -newkey rsa:2048 \
    -keyout "$SSL_DIR/key.pem" \
    -out "$SSL_DIR/cert.pem" \
    -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=$COMMON_NAME" \
    -addext "subjectAltName=DNS:$COMMON_NAME,DNS:localhost,IP:127.0.0.1"

# Set restrictive permissions
chmod 600 "$SSL_DIR/key.pem"
chmod 644 "$SSL_DIR/cert.pem"

echo ""
echo "✅ SSL certificates generated successfully!"
echo ""
echo "Files created:"
echo "  - $SSL_DIR/cert.pem (certificate)"
echo "  - $SSL_DIR/key.pem (private key)"
echo ""
echo "⚠️  These are SELF-SIGNED certificates for development only!"
echo "   For production, use certificates from a trusted CA (e.g., Let's Encrypt)"
echo ""
echo "To start the application with HTTPS:"
echo "  docker-compose up -d"
echo ""
echo "Then access: https://localhost"
