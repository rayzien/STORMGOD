$env:GITHUB_TOKEN=""
$token = gh auth token --hostname github.com -u rayzien
git remote set-url origin "https://rayzien:$($token)@github.com/rayzien/STORMGOD.git"
git -c credential.helper= push -f origin main
git remote set-url origin "https://github.com/rayzien/STORMGOD.git"
