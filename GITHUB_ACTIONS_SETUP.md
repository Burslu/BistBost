# GitHub Actions Ücretsiz Deployment 🚀

## Nedir?
GitHub'ın sunucularında bot'un **otomatik olarak her 5 dakikada çalışması** - PC'ni kapatabilirsin!

## Kurulum Adımları

### 1️⃣ GitHub Hesabı ve Repository Oluştur
```bash
# Repo var mı kontrol et
git status

# Yoksa başlat
git init
git add .
git commit -m "BIST Bot - GitHub Actions Deployment"
git branch -M main

# GitHub.com'a git, yeni repo oluştur (username/BistBot adında)
# Sonra:
git remote add origin https://github.com/USERNAME/BistBot
git push -u origin main
```

### 2️⃣ GitHub'da Secrets Ayarla
1. GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** tıkla
3. İki secret ekle:
   - **Name:** `TELEGRAM_BOT_TOKEN`
     - **Value:** `8654047508:AAG02kXiIeZjlbfN_UTlRVtYZ39-fENSxGo`
   - **Name:** `TELEGRAM_CHAT_ID`
     - **Value:** `636619118`

### 3️⃣ Workflow Dosyasını Kontrol Et
- `.github/workflows/bistbot.yml` dosyası otomatik oluşturulmuş
- Bot **her 5 dakikada** çalışacak
- **Pazartesi-Cuma, 09:30-18:00** mesai saatleri + BIST saatleriyle senkron

### 4️⃣ İlk Testi Yap
1. GitHub repo sayfasına git
2. **Actions** sekmesini aç
3. **BIST Bot Runner** workflow'u seç
4. **Run workflow** → **Run workflow** (sağ üst)
5. 1-2 dakika içinde tamamlanır

### ✅ Kontrol
- GitHub Actions çalıştığını gördüğünde → Bot başladı ✓
- Telegram mesaj alırsan (BOT ALIVE) → Başarılı ✓

## Kısıtlamalar & Avantajlar

### ✅ Avantajlar
- **Tamamen ücretsiz** 🎉
- **24/7 çalışır** (GitHub'ın sunucusu daima açık)
- **PC'ni kapatabilirsin** - bot çalışmaya devam eder
- Minimal setup

### ⚠️ Kısıtlamalar
- Aylık 2000 dakika limit (3 hafta boyunca 24/7 = ~1000 dakika)
- 5-dakikalık periyotlarla çalışır (gerçek zamanlı değil, ama yeterli)
- GitHub Actions log'u 90 gün var sonra siliniyor

## Sorun Çözme

### "Workflow başlamıyor"
- Settings → Actions → General → "Allow all actions and reusable workflows" aktif mi?

### "Telegram mesaj gelmiyor"
- Secrets doğru ayarlanmış mı? (GitHub → Settings → Secrets)
- Bot token'ı kopyaladığında fazladan boşluk var mı?

### "2000 dakika tükendi"
- Periyot'u 10 dakikaya uzat (.github/workflows/bistbot.yml'de `*/10` yap)
- Veya paid plan'a geç (Railway.app daha ucuz)

## Manuel Çalıştırma
GitHub repo → Actions → BIST Bot Runner → Run workflow

---

**Hazırsan:** 
1. `git push` yap
2. GitHub'da secrets ekle
3. Actions → Run workflow → ✅ Test et

Bot 24/7 çalışacak, hiçbir maliyeti yok! 🤖
