# app.py (V20.5 - NİHAİ TEMİZ + PYLANCE DÜZELTMELERİ!)

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time 
import random 
from flask import Flask, render_template, request, redirect, session, url_for, g, jsonify, abort 
from flask_flatpages import FlatPages
from dotenv import load_dotenv
import datetime 
import requests # Hibrit Tank için

# --- TEMEL AYARLAR ---
load_dotenv() 
app = Flask(__name__)
# KENDİ OLUŞTURDUĞUN GİZLİ ANAHTARI BURAYA YAPIŞTIR!
app.secret_key = b'\x8d\xee\x03\x9c\xb1\xa4\x0f\x0e\xcf\x8a\xdc\xb8\xe6\x1a\xe8\xe1\x1e\x9a\xf4\x8e\x01\x92\xd8\x0e' 
# app.config['SESSION_COOKIE_SECURE'] = True # Canlıya çıkınca HTTPS için açarsın

# --- BLOG AYARLARI ---
FLATPAGES_AUTO_RELOAD = True 
FLATPAGES_EXTENSION = '.md'   
FLATPAGES_ROOT = 'posts'      
FLATPAGES_MARKDOWN_EXTENSIONS = ['markdown.extensions.fenced_code', 'markdown.extensions.codehilite', 'markdown.extensions.tables'] 
app.config.from_object(__name__) 
try:
    pages = FlatPages(app) 
    print("FlatPages başarıyla yüklendi.")
except Exception as e_fp:
    print(f"!!! FlatPages yüklenirken HATA: {e_fp}. 'posts' klasörü var mı?")
    pages = None 

# --- YIL BİLGİSİ ---
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.utcnow}

# --- SPOTIFY AYARLARI ---
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI") # -> http://127.0.0.1:5000/callback olmalı
SCOPE = "user-library-read user-top-read user-read-recently-played" 
TOKEN_SESSION_KEY = "kral_token_info" 
DEFAULT_FOTO = "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg" 

# --- SESSION TABANLI KASA YÖNETİCİSİ (v17) ---
class FlaskKasaYoneticisi(spotipy.cache_handler.CacheHandler):
    # ... (Kod V20.3 ile AYNI) ...
    def __init__(self, session, anahtar_adi=TOKEN_SESSION_KEY):
        self.session = session
        self.anahtar_adi = anahtar_adi
    def get_cached_token(self):
        return self.session.get(self.anahtar_adi)
    def save_token_to_cache(self, token_info):
        print(f"Token session'a kaydedildi.")
        self.session[self.anahtar_adi] = token_info

# --- SPOTIFY OAuth OBJESİ OLUŞTURUCU ---
def get_spotify_oauth():
    # ... (Kod V20.3 ile AYNI) ...
    return SpotifyOAuth( client_id=CLIENT_ID, client_secret=CLIENT_SECRET, 
                         redirect_uri=REDIRECT_URI, scope=SCOPE, 
                         cache_handler=FlaskKasaYoneticisi(session=session) )

# --- V1 MOTORU: DNA ÇIKARICI (v15.1) ---
def extract_artist_dna_from_items(sp, items):
    # ... (Kod V20.3 ile AYNI) ...
    bilinen_track_idler = set(); artist_id_set = set()
    for item in items:
        track = item.get('track', item) 
        if track and track.get('id'):
            bilinen_track_idler.add(track['id'])
            if track.get('artists'):
                for artist in track['artists']:
                    if artist and artist.get('id'): artist_id_set.add(artist['id'])
    return bilinen_track_idler, artist_id_set

# --- V1 MOTORU: FOTOĞRAFLI HİT AVCISI (v18.1 - Max 2 Filtreli) ---
def get_kral_hit_recommendations(sp, tohum_artist_idler, orijinal_dna_filtresi, buyuyen_global_filtre, hedef_sayi):
    # ... (Kod V20.3 ile AYNI - Geveze olmayan versiyon) ...
    if not tohum_artist_idler: return [], [] 
    oneriler = []; zaten_bilinenler_sozluk = {}; artist_sayaci = {} 
    tohum_artist_listesi = list(tohum_artist_idler); random.shuffle(tohum_artist_listesi)
    print(f"\n   [V1 Motor] {len(tohum_artist_listesi)} tohum ile arama...")
    sanatci_deneme_sayaci = 0
    for artist_id in tohum_artist_listesi:
        sanatci_deneme_sayaci += 1
        if len(oneriler) >= hedef_sayi: break
        try:
            results = sp.artist_top_tracks(artist_id, country="TR") 
            if not results or not results.get('tracks'): continue
            for track in results['tracks']:
                if len(oneriler) >= hedef_sayi: break
                if not track or not track.get('id'): continue 
                track_id = track['id']; track_name = track.get('name', '?')
                artist_names_str = ", ".join([a['name'] for a in track.get('artists', [])])
                album_fotosu = DEFAULT_FOTO
                if track.get('album') and track['album'].get('images') and len(track['album']['images']) > 0:
                    album_fotosu = track['album']['images'][-1]['url'] 
                sarki_objesi = {'adi': track_name, 'sanatci': artist_names_str, 'foto': album_fotosu, 'id': track_id}
                primary_artist_name = "?"
                if track.get('artists') and track['artists'][0]['name']: primary_artist_name = track['artists'][0]['name']
                if track_id in orijinal_dna_filtresi:
                    zaten_bilinenler_sozluk[track_id] = sarki_objesi; continue 
                if track_id in buyuyen_global_filtre: continue
                current_artist_count = artist_sayaci.get(primary_artist_name, 0)
                if current_artist_count >= 2: continue 
                oneriler.append(sarki_objesi) 
                buyuyen_global_filtre.add(track_id) 
                artist_sayaci[primary_artist_name] = current_artist_count + 1
        except Exception as e: print(f"   [V1 Motor Hata] ID:{artist_id}: {e}")
        if sanatci_deneme_sayaci >= 20: break 
    print(f"   [V1 Motor] Arama bitti. {len(oneriler)} öneri.")
    return oneriler, list(zaten_bilinenler_sozluk.values())


# =======================================================
# --- ANA WEB SAYFALARI (ROUTE'LAR) ---
# =======================================================

@app.route("/")
def index():
    # --- BLOG ÖNİZLEME (DOĞRU VERSİYON - Resim Dahil!) ---
    recent_3_posts_data = [] # Obje listesi oluşturacağız
    if pages:
        try:
            latest_posts = sorted(pages, reverse=True, key=lambda p: p.meta.get('published', '1970-01-01'))
            for post in latest_posts[:3]:
                # Her post için gerekli bilgileri bir sözlüğe topla
                recent_3_posts_data.append({
                    'path': post.path,
                    'title': post.meta.get('title', 'Başlıksız'),
                    'published': post.meta.get('published', ''),
                    'author': post.meta.get('author'),
                    # Açıklama ve HTML ham olarak gidiyor, Jinja filtreleyecek
                    'description': post.meta.get('description'),
                    'html_content': post.html, # Ham HTML (truncate için)
                    # İŞTE RESİM! .md'den 'image' meta verisini al
                    'image': post.meta.get('image', DEFAULT_FOTO)
                })
        except Exception as e:
            print(f"Blog önizleme hatası: {e}")

    # Doğru listeyi (recent_3_posts_data) HTML'e yolla
    return render_template("index.html", recent_posts=recent_3_posts_data)


@app.route("/login")
def login():
    # ... (Kod V19.11 ile AYNI - Session temizle, hedefi kaydet, yönlendir) ...
    session.pop(TOKEN_SESSION_KEY, None) 
    next_url = request.args.get('next') or url_for('sonuclar') 
    session['next_url'] = next_url
    print(f"Login başlatıldı. Hedef: {next_url}")
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    # ... (Kod V19.11 ile AYNI - Token al, session'a kaydet (otomatik), hedefe yönlendir) ...
    sp_oauth = get_spotify_oauth()
    code = request.args.get('code')
    error = request.args.get('error')
    if error: print(f"Giriş hatası (Spotify'dan): {error}"); return redirect(url_for("index")) 
    try:
        sp_oauth.get_access_token(code, check_cache=False) 
        print("Token alındı ve session'a kaydedildi.")
    except spotipy.oauth2.SpotifyOauthError as e: print(f"Token alma hatası: {e}"); return redirect(url_for("index")) 
    next_url = session.pop('next_url', url_for('sonuclar')) 
    print(f"Giriş başarılı! Yönlendiriliyor: {next_url}")
    return redirect(next_url)

@app.route("/auth_required")
def auth_required():
    # ... (Kod V19.11 ile AYNI - İzin sayfasını göster) ...
    next_url = session.get('next_url', url_for('sonuclar')) 
    return render_template("auth_required.html", next_page=next_url)

# --- V1: DNA SONUÇ SAYFASI (Sadece Template Gösterir - v20) ---
@app.route("/sonuclar")
def sonuclar():
    # BASİT MUHAFIZ (v19.12 - Doğrudan session kontrolü)
    token_info = session.get(TOKEN_SESSION_KEY) 
    if not token_info:
        print("[Muhafız /sonuclar] Kasa BOŞ! İzin Odasına...")
        session['next_url'] = url_for('sonuclar')
        return redirect(url_for("auth_required"))
        
    # Sadece BOŞ sayfayı göster. JavaScript API'yi çağıracak.
    print("/sonuclar sayfası yükleniyor (JS motoru çağıracak)...")
    return render_template("sonuclar.html") 

# --- GİZLİ API: V1 Motorunu Çalıştırır (v20.3 - Düzeltilmiş) ---
@app.route("/api/v1_recommendations")
def api_v1_recommendations():
    # 1. MUHAFIZ (AYNI)
    token_info = session.get(TOKEN_SESSION_KEY) 
    if not token_info: return jsonify({"error": "Giriş gerekli."}), 401
    if token_info.get('expires_at') and token_info['expires_at'] < int(time.time()):
         session.pop(TOKEN_SESSION_KEY, None); return jsonify({"error": "Oturum doldu.", "login_required": True}), 401
         
    # 2. ELÇİ (AYNI)
    try: sp = spotipy.Spotify(auth=token_info['access_token'])
    except Exception as e: return jsonify({"error": f"Spotify bağlantı hatası: {e}"}), 500

    print("API (/api/v1_recommendations) çağrıldı. V1 Motoru çalışıyor...")
    # 3. V1 MOTOR MANTIĞI (v20.3 Düzeltmesiyle)
    try:
        # BİLGİ METNİ (AYNI)
        top_artist_name = "?"; kayitli_sarki_sayisi = 0
        try:
            top_artist_result = sp.current_user_top_artists(limit=1, time_range='medium_term')
            if top_artist_result and top_artist_result.get('items'): top_artist_name = top_artist_result['items'][0]['name']
        except Exception as e: print(f"API: Top artist çekilemedi: {e}")

        # MODÜLLER (v20.3 Düzeltmesiyle)
        m1_tracks, m1_artists = set(), set(); m2_tracks, m2_artists = set(), set(); m3_tracks, m3_artists = set(), set()
        try: # M1
            saved_tracks_items = []; results = sp.current_user_saved_tracks(limit=50)
            while True: 
                items = results.get('items', []); 
                if not items: break 
                saved_tracks_items.extend(items)
                if not results.get('next'): break 
                results = sp.next(results) 
            m1_tracks, m1_artists = extract_artist_dna_from_items(sp, saved_tracks_items)
            print(f"API [M1] {len(m1_tracks)} şarkı.")
        except Exception as e: print(f"API Hata M1: {e}")
        kayitli_sarki_sayisi = len(m1_tracks) 
        try: # M2
            results = sp.current_user_top_tracks(limit=50, time_range='medium_term')
            m2_tracks, m2_artists = extract_artist_dna_from_items(sp, results.get('items', [])) 
            print(f"API [M2] {len(m2_tracks)} şarkı.")
        except Exception as e: print(f"API Hata M2: {e}")
        try: # M3
            results = sp.current_user_recently_played(limit=50)
            m3_tracks, m3_artists = extract_artist_dna_from_items(sp, results.get('items', []))
            print(f"API [M3] {len(m3_tracks)} şarkı.")
        except Exception as e: print(f"API Hata M3: {e}")
            
        # FİLTRELER VE MOTOR ÇAĞRILARI (AYNI)
        orijinal_dna_filtresi = m1_tracks.union(m2_tracks).union(m3_tracks)
        global_filtre_ve_yeni_oneriler = orijinal_dna_filtresi.copy() 
        tum_favori_sanatcilar = m1_artists.union(m2_artists).union(m3_artists)
        tum_bonus_sarkilar_sozluk = {}
        
        oneriler_genel, bonus_genel = get_kral_hit_recommendations(sp, tum_favori_sanatcilar, orijinal_dna_filtresi, global_filtre_ve_yeni_oneriler, 9)
        for sarki_obj in bonus_genel: tum_bonus_sarkilar_sozluk[sarki_obj['id']] = sarki_obj
        oneriler_top, bonus_top = get_kral_hit_recommendations(sp, m2_artists, orijinal_dna_filtresi, global_filtre_ve_yeni_oneriler, 9) 
        for sarki_obj in bonus_top: tum_bonus_sarkilar_sozluk[sarki_obj['id']] = sarki_obj
        oneriler_recent, bonus_recent = get_kral_hit_recommendations(sp, m3_artists, orijinal_dna_filtresi, global_filtre_ve_yeni_oneriler, 9) 
        for sarki_obj in bonus_recent: tum_bonus_sarkilar_sozluk[sarki_obj['id']] = sarki_obj
        
        bonus_listesi = list(tum_bonus_sarkilar_sozluk.values())
        if len(bonus_listesi) > 5: bonus_listesi = random.sample(bonus_listesi, 5)
        
        print("API Analizi bitti! JSON gönderiliyor.")
        # 4. SONUÇLARI JSON OLARAK DÖNDÜR!
        return jsonify({ "success": True, "kayitli_sayisi": kayitli_sarki_sayisi, "top_sanatci": top_artist_name,
                         "genel_liste": oneriler_genel, "top_liste": oneriler_top, 
                         "recent_liste": oneriler_recent, "bonus_liste": bonus_listesi })
    # HATA YAKALAMA (AYNI)
    except spotipy.exceptions.SpotifyException as se:
         print(f"API Hatası (Spotify): {se}"); 
         if se.http_status == 401: session.pop(TOKEN_SESSION_KEY, None); return jsonify({"error": "Oturum doldu.", "login_required": True}), 401
         else: return jsonify({"error": f"Spotify Hatası: {se.msg}"}), se.http_status or 500
    except Exception as e: print(f"API Hatası (Genel): {e}"); return jsonify({"error": f"Sunucu hatası: {e}"}), 500

# --- V2: ŞARKICI ARAMA SAYFASI ---
@app.route("/artist_search")
def artist_search():
    # BASİT MUHAFIZ (AYNI)
    token_info = session.get(TOKEN_SESSION_KEY) 
    if not token_info:
        print("[Muhafız /artist_search] Kasa BOŞ! İzin Odasına...")
        session['next_url'] = url_for('artist_search') 
        return redirect(url_for("auth_required"))
    return render_template("artist_search.html")

# --- V2: ŞARKICI ÖNERİ MOTORU (HİBRİT TANK v19.10 - Foto Tamirli) ---
# (Pylance hataları için try/except blokları eklendi/düzeltildi)
@app.route("/artist_recommend", methods=["POST"])
def artist_recommend():
    # 1. GİRİŞ KONTROLÜ VE TOKEN YENİLEME (AYNI)
    sp_oauth = get_spotify_oauth(); token_info = sp_oauth.get_cached_token()
    if not token_info: session['next_url'] = url_for('artist_search'); return redirect(url_for("auth_required"))
    if token_info.get('expires_at') and token_info['expires_at'] < int(time.time()):
        try: token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        except Exception as e: print(f"Token yenileme hatası: {e}"); return redirect(url_for("login")) 
    access_token = token_info['access_token'] 

    # 2. ARAMA KUTUSU VERİSİ (AYNI)
    artist_query = request.form.get('artist_query'); 
    if not artist_query: return redirect(url_for('artist_search'))
    print(f"Yeni 'Hibrit Tank (v20.5)' araması başladı. Aranan: {artist_query}")

    # 3. MERKEZİ BUL (Requests ile - AYNI)
    center_artist_data = None; related_artists_list = []; center_artist_id = None; center_genres = []
    try:
        search_url = "https://api.spotify.com/v1/search"; headers = {"Authorization": f"Bearer {access_token}"}
        params = {'q': artist_query, 'type': 'artist', 'limit': 1}; print(f"🔍 Merkez Arama: q='{artist_query}'")
        response = requests.get(search_url, headers=headers, params=params); response.raise_for_status() 
        search_results_raw = response.json()
        if not search_results_raw['artists']['items']: return render_template("artist_search.html", error_mesaji=f"'{artist_query}' bulunamadı.")
        center_artist = search_results_raw['artists']['items'][0]
        center_artist_id = center_artist.get('id'); center_genres = center_artist.get('genres', [])
        print(f"--- MERKEZ BULUNDU ---> ADI: {center_artist.get('name', '?')}, ID: {center_artist_id} ---") 
        if not center_artist_id: return render_template("artist_search.html", error_mesaji="Sanatçı ID'si alınamadı.")
        center_foto = DEFAULT_FOTO
        if center_artist.get('images') and len(center_artist['images']) > 0: center_foto = center_artist['images'][0]['url']
        center_artist_data = { 'adi': center_artist.get('name','?'), 'foto': center_foto, 'id': center_artist_id, 'turler': center_genres }
        
        # --- HİBRİT TANK PLANI ---
        plan_a_basarili = False
        # --- PLAN A (Requests ile - AYNI) ---
        try: # PYLANCE HATASI İÇİN TRY EKLE!
            print(f"[Plan A - Requests] Başladı...")
            related_url = f"https://api.spotify.com/v1/artists/{center_artist_id}/related-artists" 
            response_related = requests.get(related_url, headers=headers); response_related.raise_for_status() 
            related_results_raw = response_related.json()
            if related_results_raw and related_results_raw.get('artists'):
                for artist in related_results_raw['artists']:
                    artist_foto = DEFAULT_FOTO
                    if artist.get('images') and len(artist['images']) > 0: artist_foto = artist['images'][-1]['url']
                    if len(related_artists_list) < 10: related_artists_list.append({'adi': artist.get('name','?'), 'foto': artist_foto})
                    else: break 
                if related_artists_list: plan_a_basarili = True; print(f"[Plan A] BAŞARILI! {len(related_artists_list)}")
                else: print("[Plan A] Başarısız: Liste boş.")
            else: print("[Plan A] Başarısız: Sonuç boş.")
        except requests.exceptions.HTTPError as http_err: print(f"[Plan A] HAYALET! {http_err}")
        except requests.exceptions.RequestException as req_err: print(f"[Plan A] Bağlantı Hatası: {req_err}")
        except Exception as e: print(f"[Plan A] Genel Hata: {e}")

        # --- PLAN B & C İÇİN SPOTIPY ELÇİSİ ---
        sp = None
        if not plan_a_basarili:
             try: sp = spotipy.Spotify(auth=access_token)
             except Exception as e_sp: print(f"Plan B/C elçi hatası: {e_sp}")

        # --- PLAN B (Spotipy ile - AYNI) ---
        plan_b_basarili = False
        if not plan_a_basarili and sp: 
            try: # PYLANCE HATASI İÇİN TRY EKLE!
                print(f"[Plan B - Spotipy] Başladı...")
                if not center_genres: print("[Plan B] Tür yok.")
                else:
                    first_genre = center_genres[0]
                    related_artists_found_b = {}
                    try:
                        query = f'genre:"{first_genre}"'; print(f"[Plan B] Tür: '{first_genre}'. Arama...")
                        genre_search = sp.search(q=query, type='artist', limit=11, market='TR') 
                        items = genre_search.get('artists', {}).get('items', [])
                        print(f"[Plan B] '{first_genre}' için {len(items)} sonuç.")
                        if items:
                            found_count = 0
                            for artist in items:
                                if artist['id'] != center_artist_id: 
                                    artist_foto = DEFAULT_FOTO
                                    if artist.get('images') and len(artist['images']) > 0: artist_foto = artist['images'][-1]['url']
                                    related_artists_found_b[artist['id']] = {'adi': artist['name'], 'foto': artist_foto}
                                    found_count += 1
                                    if found_count >= 10: break 
                            temp_list = list(related_artists_found_b.values())
                            if temp_list: plan_b_basarili = True; related_artists_list = temp_list; print(f"[Plan B] BAŞARILI! {len(related_artists_list)}")
                            else: print(f"[Plan B] Başarısız: Merkez hariç sonuç yok.")
                        else: print(f"[Plan B] Başarısız: Arama boş.")
                    except Exception as e_search: print(f"[Plan B] Arama hatası: {e_search}")
            except Exception as e_b: print(f"[Plan B] Genel Hata: {e_b}")

        # --- PLAN C (Spotipy ile - Foto Tamirli - AYNI) ---
        if not plan_a_basarili and not plan_b_basarili and sp: 
            try: # PYLANCE HATASI İÇİN TRY EKLE!
                print(f"[Plan C - Spotipy] Başladı...")
                top = sp.artist_top_tracks(center_artist_id, country='TR') 
                if top and top.get('tracks'):
                    seen = set(); temp_list_c = []
                    for t in top['tracks']:
                        for a in t.get('artists', []):
                            if a['id'] != center_artist_id and a['id'] not in seen:
                                seen.add(a['id']); artist_foto = DEFAULT_FOTO
                                try: # Foto çekmeyi deneyelim (iç try-except)
                                    artist_full = sp.artist(a['id'])
                                    if artist_full.get('images') and len(artist_full['images']) > 0: artist_foto = artist_full['images'][-1]['url']
                                except Exception as e_foto: print(f"Plan C foto hatası ({a['name']}): {e_foto}") # Sadece logla
                                temp_list_c.append({'adi': a['name'], 'foto': artist_foto})
                                if len(temp_list_c) >= 8: break 
                        if len(temp_list_c) >= 8: break
                    if temp_list_c: related_artists_list = temp_list_c; print(f"[Plan C] BAŞARILI! {len(related_artists_list)}")
                    else: print("[Plan C] Başarısız: Sonuç yok.")
                else: print("[Plan C] Başarısız: Sonuç yok.")
            except Exception as e_c: print(f"[Plan C] Hata: {e_c}")

    # --- ANA HATA YAKALAMA (AYNI) ---
    except Exception as e:
        print(f"KRALİYET HATASI! Motor patladı: {e}")
        return render_template("artist_search.html", error_mesaji=f"Motor hatası: {e}")

    # YEDEK MESAJ (AYNI)
    if not related_artists_list:
         print("Sonuç: Hiçbir plan işe yaramadı.")
         related_artists_list.append({'adi': 'Benzer sanatçı bulunamadı 😢'})

    # HTML'e GÖNDER (AYNI)
    print(f"--- HTML'e GÖNDERİLİYOR ---> Merkez: {center_artist_data.get('adi','?')}, Öneri Sayısı: {len(related_artists_list)} ---")
    return render_template("artist_results.html",
                           center_artist=center_artist_data,
                           related_list=related_artists_list)


# =======================================================
# --- BLOG SAYFALARI (v20.4 - Tag Fonksiyonu Dahil) ---
# =======================================================
@app.route('/blog/')
def blog_index():
    # ... (Kod V20.4 ile AYNI - Tag filtresi dahil) ...
    latest_posts = []
    tag_filter = request.args.get('tag') 
    if pages:
        try:
            if tag_filter: 
                 posts_query = [p for p in pages if tag_filter.lower() in [t.lower() for t in p.meta.get('tags', [])]]
                 print(f"Blog: '{tag_filter}' etiketi için {len(posts_query)} yazı bulundu.")
            else: 
                 posts_query = pages
                 print(f"Blog: Toplam {len(list(pages))} yazı bulundu.")
            latest_posts = sorted(posts_query, reverse=True, key=lambda p: p.meta.get('published', '1970-01-01'))
        except Exception as e: print(f"Blog listeleme hatası: {e}")
    return render_template('blog_index.html', posts=latest_posts, tag_name=tag_filter) 

@app.route('/blog/<path:path>/') 
def blog_post(path):
    # ... (Kod V20.4 ile AYNI) ...
    if not pages: abort(404) 
    post = pages.get_or_404(path)
    return render_template('post.html', post=post)

# TAG ARŞİVİ FONKSİYONU (V20.4'ten)
@app.route('/blog/tag/<tag>/')
def tag_archive(tag):
    # ... (Kod V20.4 ile AYNI) ...
    if not pages: return "Blog sistemi yüklenemedi.", 500
    try:
        tag_lower = tag.lower()
        tagged_posts = [p for p in pages if tag_lower in [t.lower() for t in p.meta.get('tags', [])]]
        print(f"Blog Tag: '{tag}' için {len(tagged_posts)} yazı bulundu.")
        tagged_posts.sort(key=lambda p: p.meta.get('published', '1970-01-01'), reverse=True)
        return render_template('blog_index.html', posts=tagged_posts, tag_name=tag)
    except Exception as e: print(f"Tag arşivi hatası ('{tag}'): {e}"); return f"'{tag}' etiketi hatası.", 500

# =======================================================
# --- DİĞER SAYFALAR (v19.12) ---
# =======================================================
@app.route('/about')
def about(): return render_template('about.html')
@app.route('/contact')
def contact(): return render_template('contact.html')

# =======================================================
# --- SUNUCUYU BAŞLAT ---
# =======================================================
