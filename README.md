# Öğrenci–Danışman Görüşme ve Proje Takip Sistemi

Öğrenci grupları ile danışman öğretim üyeleri arasındaki görüşme, görev, teslim ve geri bildirim süreçlerini tek ortamda yöneten web uygulaması.

## Teknolojiler
- Python, Django
- SQLite

## Kurulum
1. Sanal ortam oluşturun: `python -m venv venv`
2. Etkinleştirin: `.\venv\Scripts\Activate.ps1`
3. Paketleri kurun: `pip install -r requirements.txt`
4. Tabloları oluşturun: `python manage.py migrate`
5. Çalıştırın: `python manage.py runserver`

## Modeller
Kullanici, ProjeGrubu, GrupUyesi, MusaitlikSlotu, GorusmeTalebi, Gorev, Teslim, GeriBildirim, Bildirim

## Proje yönetimi
İş takibi Jira üzerinden yapılmaktadır. Commit mesajları ilgili Jira kaydının numarasıyla (SVT-xx) başlar.