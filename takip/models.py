from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models


class Kullanici(models.Model):
    ROLLER = [('ogrenci', 'Öğrenci'), ('danisman', 'Danışman')]

    kullanici_id = models.AutoField(primary_key=True)
    ad_soyad = models.CharField(max_length=150)
    eposta = models.EmailField(unique=True)
    sifre_hash = models.CharField(max_length=255)
    rol = models.CharField(max_length=10, choices=ROLLER)

    class Meta:
        db_table = 'KULLANICI'

    def __str__(self):
        return f'{self.ad_soyad} ({self.rol})'


class ProjeGrubu(models.Model):
    grup_id = models.AutoField(primary_key=True)
    proje_adi = models.CharField(max_length=200)
    aciklama = models.TextField(blank=True)
    # Danışman grup oluştuktan sonra eşleşir, boş olabilir
    danisman = models.ForeignKey(
        Kullanici, null=True, blank=True, on_delete=models.SET_NULL,
        limit_choices_to={'rol': 'danisman'}, related_name='danismanlik_gruplari',
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'PROJE_GRUBU'

    def __str__(self):
        return self.proje_adi


class GrupUyesi(models.Model):
    grup = models.ForeignKey(ProjeGrubu, on_delete=models.CASCADE, related_name='uyeler')
    # Öğrenci tek gruba üye olur
    ogrenci = models.OneToOneField(
        Kullanici, on_delete=models.CASCADE,
        limit_choices_to={'rol': 'ogrenci'}, related_name='grup_uyeligi',
    )
    katilma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'GRUP_UYESI'
        constraints = [
            models.UniqueConstraint(fields=['grup', 'ogrenci'], name='uniq_grup_ogrenci'),
        ]

    def clean(self):
        # Grup en fazla 2 üyelidir
        if self._state.adding and GrupUyesi.objects.filter(grup=self.grup).count() >= 2:
            raise ValidationError('Bir grup en fazla 2 öğrenci içerebilir.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.grup} - {self.ogrenci}'


class MusaitlikSlotu(models.Model):
    DURUMLAR = [('bos', 'Boş'), ('dolu', 'Dolu'), ('iptal', 'İptal')]

    slot_id = models.AutoField(primary_key=True)
    danisman = models.ForeignKey(
        Kullanici, on_delete=models.CASCADE,
        limit_choices_to={'rol': 'danisman'}, related_name='musaitlik_slotlari',
    )
    baslangic = models.DateTimeField()
    bitis = models.DateTimeField()
    durum = models.CharField(max_length=10, choices=DURUMLAR, default='bos')

    class Meta:
        db_table = 'MUSAITLIK_SLOTU'

    def clean(self):
        if self.baslangic and self.bitis and self.bitis <= self.baslangic:
            raise ValidationError('Bitiş, başlangıçtan sonra olmalıdır.')

    def __str__(self):
        return f'{self.danisman} {self.baslangic:%d.%m.%Y %H:%M}'


class GorusmeTalebi(models.Model):
    DURUMLAR = [
        ('beklemede', 'Beklemede'), ('onaylandi', 'Onaylandı'),
        ('reddedildi', 'Reddedildi'), ('iptal', 'İptal'),
    ]

    talep_id = models.AutoField(primary_key=True)
    slot = models.ForeignKey(MusaitlikSlotu, on_delete=models.CASCADE, related_name='talepler')
    grup = models.ForeignKey(ProjeGrubu, on_delete=models.CASCADE, related_name='gorusme_talepleri')
    konu = models.CharField(max_length=200)
    durum = models.CharField(max_length=12, choices=DURUMLAR, default='beklemede')
    ret_gerekcesi = models.TextField(blank=True)
    olusturma_zamani = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'GORUSME_TALEBI'

    def __str__(self):
        return f'{self.grup} - {self.konu}'


class Gorev(models.Model):
    DURUMLAR = [
        ('yapilacak', 'Yapılacak'), ('teslim_edildi', 'Teslim edildi'),
        ('duzeltme_istendi', 'Düzeltme istendi'), ('onaylandi', 'Onaylandı'),
    ]

    gorev_id = models.AutoField(primary_key=True)
    grup = models.ForeignKey(ProjeGrubu, on_delete=models.CASCADE, related_name='gorevler')
    baslik = models.CharField(max_length=200)
    aciklama = models.TextField(blank=True)
    son_teslim_tarihi = models.DateTimeField()
    durum = models.CharField(max_length=20, choices=DURUMLAR, default='yapilacak')

    class Meta:
        db_table = 'GOREV'

    def __str__(self):
        return self.baslik


class Teslim(models.Model):
    DURUMLAR = [
        ('teslim_edildi', 'Teslim edildi'),
        ('duzeltme_istendi', 'Düzeltme istendi'),
        ('onaylandi', 'Onaylandı'),
    ]

    teslim_id = models.AutoField(primary_key=True)
    gorev = models.ForeignKey(Gorev, on_delete=models.CASCADE, related_name='teslimler')
    # Her sürüm ayrı satırdır, eski sürümler silinmez
    versiyon_no = models.PositiveIntegerField(default=1)
    # Dosya depolama kapsam dışı: yalnızca dosya adı tutulur
    dosya_adi = models.CharField(max_length=255)
    yuklenme_zamani = models.DateTimeField(auto_now_add=True)
    durum = models.CharField(max_length=20, choices=DURUMLAR, default='teslim_edildi')

    class Meta:
        db_table = 'TESLIM'
        constraints = [
            models.UniqueConstraint(fields=['gorev', 'versiyon_no'], name='uniq_gorev_versiyon'),
        ]

    def __str__(self):
        return f'{self.gorev} v{self.versiyon_no}'


class GeriBildirim(models.Model):
    KARARLAR = [('onay', 'Onay'), ('duzeltme', 'Düzeltme')]

    geri_bildirim_id = models.AutoField(primary_key=True)
    teslim = models.ForeignKey(Teslim, on_delete=models.CASCADE, related_name='geri_bildirimler')
    yorum = models.TextField(blank=True)
    not_degeri = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MaxValueValidator(100)],
    )
    karar = models.CharField(max_length=10, choices=KARARLAR)
    olusturma_zamani = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'GERI_BILDIRIM'

    def __str__(self):
        return f'{self.teslim} - {self.karar}'


class Bildirim(models.Model):
    bildirim_id = models.AutoField(primary_key=True)
    alici = models.ForeignKey(Kullanici, on_delete=models.CASCADE, related_name='bildirimler')
    mesaj = models.TextField()
    okundu = models.BooleanField(default=False)
    olusturma_zamani = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'BILDIRIM'

    def __str__(self):
        return self.mesaj[:40]