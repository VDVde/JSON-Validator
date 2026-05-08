# PowerShell script to generate self-signed SSL certificates for Windows
# Usage: .\generate-ssl-certs.ps1 [hostname]

param(
    [string]$CommonName = "localhost"
)

$SSLDir = "nginx\ssl"
$Days = 365

Write-Host "🔐 Generating SSL certificates for: $CommonName" -ForegroundColor Cyan

# Create SSL directory if it doesn't exist
if (-not (Test-Path $SSLDir)) {
    New-Item -ItemType Directory -Path $SSLDir -Force | Out-Null
}

# Check if OpenSSL is available
$opensslPath = Get-Command openssl -ErrorAction SilentlyContinue

if ($opensslPath) {
    # Use OpenSSL if available (preferred)
    Write-Host "Using OpenSSL..." -ForegroundColor Yellow
    
    $certFile = Join-Path $SSLDir "cert.pem"
    $keyFile = Join-Path $SSLDir "key.pem"
    
    # Generate certificate with SAN (no backticks to avoid parsing issues)
    openssl req -x509 -nodes -days $Days -newkey rsa:2048 -keyout $keyFile -out $certFile -subj "/C=DE/ST=Germany/L=Berlin/O=VDV463 Validator/CN=$CommonName" -addext "subjectAltName=DNS:$CommonName,DNS:localhost,IP:127.0.0.1"
    
    Write-Host ""
    Write-Host "✅ SSL certificates generated with OpenSSL!" -ForegroundColor Green
    
}
else {
    # Use PowerShell New-SelfSignedCertificate as fallback
    Write-Host "OpenSSL not found, using PowerShell..." -ForegroundColor Yellow
    
    # Generate self-signed certificate
    $cert = New-SelfSignedCertificate -DnsName $CommonName, "localhost" -CertStoreLocation "cert:\CurrentUser\My" -NotAfter (Get-Date).AddDays($Days) -KeyAlgorithm RSA -KeyLength 2048 -HashAlgorithm SHA256 -FriendlyName "VDV463 Validator Development"
    
    # Export certificate (public key)
    $certPath = Join-Path $SSLDir "cert.pem"
    $certBytes = $cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
    $certBase64 = [System.Convert]::ToBase64String($certBytes)
    $certPem = "-----BEGIN CERTIFICATE-----" + "`n"
    for ($i = 0; $i -lt $certBase64.Length; $i += 64) {
        $certPem += $certBase64.Substring($i, [Math]::Min(64, $certBase64.Length - $i)) + "`n"
    }
    $certPem += "-----END CERTIFICATE-----"
    Set-Content -Path $certPath -Value $certPem -NoNewline
    
    # Export private key
    $pfxPath = Join-Path $SSLDir "temp.pfx"
    $password = ConvertTo-SecureString -String "temp" -Force -AsPlainText
    Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $password | Out-Null
    
    # Use OpenSSL in Docker to convert PFX to PEM
    $dockerPath = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerPath) {
        docker run --rm -v "${PWD}/${SSLDir}:/ssl" alpine/openssl pkcs12 -in /ssl/temp.pfx -nocerts -nodes -out /ssl/key.pem -passin pass:temp
        Remove-Item $pfxPath -Force
        Write-Host "✅ SSL certificates generated!" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  Certificate generated, but private key conversion requires Docker or OpenSSL" -ForegroundColor Yellow
        Write-Host "    Install OpenSSL: winget install OpenSSL" -ForegroundColor Yellow
    }
    
    # Remove cert from store
    Remove-Item "cert:\CurrentUser\My\$($cert.Thumbprint)" -Force
}

Write-Host ""
Write-Host "Files created:" -ForegroundColor White
Write-Host "  - $SSLDir\cert.pem (certificate)" -ForegroundColor Gray
Write-Host "  - $SSLDir\key.pem (private key)" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  These are SELF-SIGNED certificates for development only!" -ForegroundColor Yellow
Write-Host "   For production, use certificates from a trusted CA." -ForegroundColor Yellow
Write-Host ""
Write-Host "To start the application with HTTPS:" -ForegroundColor Cyan
Write-Host "  docker compose up -d" -ForegroundColor White
Write-Host ""
Write-Host "Then access: https://localhost" -ForegroundColor Green
