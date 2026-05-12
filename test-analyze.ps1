$body = @{
    contract_text = "This is a test contract for employment"
    contract_type = "general"
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://localhost:8001/api/v1/analyze' -Method POST -ContentType 'application/json' -Body $body