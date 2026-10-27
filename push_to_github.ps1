# push_to_github.ps1 - create the GitHub repo and push this repository.
#
#   $env:GITHUB_TOKEN = "ghp_xxx"
#   .\push_to_github.ps1 -Repo tare-breaker -Private
#
# Token scopes needed: repo (classic) or Contents+Administration (fine-grained).
# The token is used for one push and is NOT written into .git/config.
param(
    [string]$Repo = "Tare-breaker",
    [string]$User = "lauyangiiii",
    [string]$Description = "tare-breaker 0.1.0 - adversarial prompt evaluation harness: 16 structures x 15 mutations x refusal scoring x beam search",
    [switch]$Private,
    [switch]$SkipCreate
)

$ErrorActionPreference = "Stop"

if (-not $env:GITHUB_TOKEN) { throw "GITHUB_TOKEN is not set." }
$token = $env:GITHUB_TOKEN

$headers = @{
    Authorization          = "Bearer $token"
    Accept                 = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
    "User-Agent"           = "tare-breaker-push"
}

if (-not $User) {
    $me = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers
    $User = $me.login
    Write-Host "authenticated as: $User"
}

# ---------------------------------------------------------------- 1. create repo
$body = @{
    name        = $Repo
    description = $Description
    private     = [bool]$Private
    has_issues  = $true
    has_wiki    = $false
} | ConvertTo-Json

if ($SkipCreate) {
    Write-Host "skip create, pushing to existing repo: https://github.com/$User/$Repo"
} else {
    try {
        $created = Invoke-RestMethod -Method Post -Uri "https://api.github.com/user/repos" `
            -Headers $headers -Body $body -ContentType "application/json"
        Write-Host "repo created: $($created.html_url)"
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        if ($code -eq 422) {
            Write-Host "repo already exists, reusing: https://github.com/$User/$Repo"
        } else {
            throw
        }
    }
}

# ---------------------------------------------------------------- 2. push
Set-Location $PSScriptRoot
$remote = "https://github.com/$User/$Repo.git"
$authRemote = "https://x-access-token:$token@github.com/$User/$Repo.git"

git remote remove origin 2>$null
git remote add origin $remote
git config http.sslBackend openssl

Write-Host "pushing main ..."
git push $authRemote main:main
if ($LASTEXITCODE -ne 0) { throw "push failed" }

if ((git tag) -ne $null) {
    Write-Host "pushing tags ..."
    git push $authRemote --tags
}

# ---------------------------------------------------------------- 3. verify
git remote set-url origin $remote
$check = git ls-remote $remote 2>&1
Write-Host ""
Write-Host "done:"
Write-Host "  https://github.com/$User/$Repo"
Write-Host ("  refs: " + (($check | Measure-Object).Count) + " lines from ls-remote")
