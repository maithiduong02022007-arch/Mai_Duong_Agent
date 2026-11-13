# Máy chủ HTTP Localhost cho CRM AI Agent Minh An (PowerShell tích hợp sẵn trên Windows)
$port = 8080
$prefix = "http://localhost:$port/"
$rootPath = $PSScriptRoot

if (-not $rootPath) {
    $rootPath = Get-Location
}

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add($prefix)

try {
    $listener.Start()
} catch {
    Write-Host "Không thể mở cổng $port. Vui lòng kiểm tra quyền hoặc cổng đã bị chiếm dụng." -ForegroundColor Red
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " MINH AN TECHNOLOGY - AI AGENT CRM SYSTEM (LOCALHOST)" -ForegroundColor Green
Write-Host " Đang phục vụ tại: $prefix" -ForegroundColor Yellow
Write-Host " Nhấn Ctrl + C để dừng máy chủ." -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan

# Mở trình duyệt mặc định
Start-Process $prefix

while ($listener.IsListening) {
    try {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response

        $urlPath = $request.Url.LocalPath
        if ($urlPath -eq "/" -or [string]::IsNullOrWhiteSpace($urlPath)) {
            $urlPath = "/index.html"
        }

        $filePath = Join-Path $rootPath $urlPath.TrimStart('/')

        if (Test-Path $filePath -PathType Leaf) {
            $bytes = [System.IO.File]::ReadAllBytes($filePath)
            
            # Content type detection
            if ($filePath.EndsWith(".html")) {
                $response.ContentType = "text/html; charset=utf-8"
            } elseif ($filePath.EndsWith(".js")) {
                $response.ContentType = "application/javascript; charset=utf-8"
            } elseif ($filePath.EndsWith(".css")) {
                $response.ContentType = "text/css; charset=utf-8"
            } elseif ($filePath.EndsWith(".json")) {
                $response.ContentType = "application/json; charset=utf-8"
            } else {
                $response.ContentType = "application/octet-stream"
            }

            $response.ContentLength64 = $bytes.Length
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
        } else {
            $response.StatusCode = 404
            $errBytes = [System.Text.Encoding]::UTF8.GetBytes("404 Not Found")
            $response.OutputStream.Write($errBytes, 0, $errBytes.Length)
        }
        $response.Close()
    } catch {
        # Bỏ qua lỗi ngắt kết nối client
    }
}

