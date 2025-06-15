import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from collections import Counter
from itertools import combinations
import matplotlib.pyplot as plt
import random
from db import init_db, zapisz_wyniki_do_bazy, pobierz_wszystkie_wyniki
# 🔐 API klucz (opcjonalny)
API_KEY = "TWOJ_KLUCZ_API_TUTAJ"
API_HEADERS = {"accept": "application/json", "secret": API_KEY}
API_BASE = "https://developers.lotto.pl/api/open/v1/"

# 📎 Stały link do CSV
STAŁY_CSV_URL = "https://www.wynikilotto.net.pl/download/lotto.csv"

def pobierz_z_api(limit=200, game="Lotto"):
    url = f"{API_BASE}lotteries/draws/latest?gameType={game}&cnt={limit}"
    try:
        r = requests.get(url, headers=API_HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        wyniki = [w['numbers'] for w in data if 'numbers' in w]
        st.info("📡 Dane pobrane z API Lotto")
        return wyniki
    except Exception as e:
        st.warning(f"API Lotto niedostępne. ({e})")
        return None

def pobierz_z_html(strony=20):
    url_base = "https://www.lotto.pl/lotto/wyniki-i-wygrane/archiwum?sort=desc&page="
    headers = {"User-Agent": "Mozilla/5.0"}
    wyniki = []

    for i in range(1, strony + 1):
        try:
            r = requests.get(url_base + str(i), headers=headers, timeout=10)
            soup = BeautifulSoup(r.content, "html.parser")
            losowania = soup.find_all("li", class_="results-item")
            if not losowania:
                break

            for los in losowania:
                liczby_div = los.find_all("span", class_="numbers-box__number")
                liczby = [int(l.text.strip()) for l in liczby_div[:6]]
                if len(liczby) == 6:
                    wyniki.append(liczby)
            time.sleep(1)
        except Exception as e:
            st.error(f"Błąd pobierania strony {i}: {e}")
            continue

    if wyniki:
        st.info("🧾 Dane pobrane ze strony lotto.pl (scraper)")
    return wyniki

def pobierz_z_csv(url):
    try:
        df = pd.read_csv(url)
        #df = df.apply(pd.to_numeric, errors='coerce')  # Konwersja wszystkiego na liczby
        #df = df.dropna(axis=0, how="any")               # Usuń wiersze z NaN

        if df.shape[1] < 6:
            st.error("CSV musi zawierać co najmniej 6 kolumn z liczbami.")
            return None

        # 🔽 Weź tylko 6 ostatnich kolumn
        df = df.iloc[:, -6:]

        # 🔍 Filtr: tylko liczby od 1 do 49
        df = df[(df >= 1) & (df <= 49)]
        df = df.dropna().astype(int)

        wyniki = df.values.tolist()
        if not wyniki:
            st.error("Nie znaleziono żadnych prawidłowych zestawów 6 liczb (1–49).")
            return None

        st.info("📁 Dane z CSV: ostatnie 6 kolumn, liczby 1–49")
        return wyniki

    except Exception as e:
        st.error(f"❌ Błąd wczytywania CSV: {e}")
        return None


def analiza_lotto(wyniki):
    df = pd.DataFrame(wyniki, columns=["L1", "L2", "L3", "L4", "L5", "L6"])
    st.success(f"Pobrano {len(df)} losowań.")
    st.dataframe(df.head())

    wszystkie = df.values.flatten()
    licznik = Counter(wszystkie)
    najczestsze = licznik.most_common(10)

    st.subheader("🔢 Najczęściej losowane liczby")
    for l, n in najczestsze:
        st.write(f"Liczba {l}: {n} razy")

    st.subheader("📈 Histogram popularności liczb")
    liczby = sorted(licznik.items())
    if liczby:
        x, y = zip(*liczby)
        fig, ax = plt.subplots()
        ax.bar(x, y)
        ax.set_xlabel("Liczby")
        ax.set_ylabel("Ilość losowań")
        st.pyplot(fig)
    else:
        st.warning("Brak danych do histogramu.")
        st.subheader("📊 Wykres prawdopodobieństwa wystąpienia liczby")

    liczba_losowan = len(wyniki)
    prawdopodobienstwa = {l: n / liczba_losowan for l, n in licznik.items()}
    prawdopodobienstwa = dict(sorted(prawdopodobienstwa.items()))  # sortuj rosnąco po liczbie

    x = list(prawdopodobienstwa.keys())
    y = list(prawdopodobienstwa.values())

    fig, ax = plt.subplots()
    ax.plot(x, y, 'red')
    ax.set_xlabel("Liczba (1–49)")
    ax.set_ylabel("Prawdopodobieństwo")
    ax.set_title("Szacowane prawdopodobieństwo wystąpienia liczby")
    st.pyplot(fig)
    
    #Analiza trendów
    st.subheader("📊 Trendy liczbowych częstotliwości (dawniej vs. teraz)")

    polowa = len(wyniki) // 2
    pierwsza_pol = [n for row in wyniki[:polowa] for n in row]
    druga_pol = [n for row in wyniki[polowa:] for n in row]

    licznik_stare = Counter(pierwsza_pol)
    licznik_nowe = Counter(druga_pol)

    trend_data = []
    for liczba in range(1, 50):
        stare = licznik_stare.get(liczba, 0)
        nowe = licznik_nowe.get(liczba, 0)
        roznica = nowe - stare
        trend_data.append((liczba, roznica))

    trend_data.sort(key=lambda x: x[1], reverse=True)

    st.write("🔼 Liczby z największym wzrostem:")
    for liczba, zmiana in trend_data[:10]:
        st.write(f"Liczba {liczba}: +{zmiana} porównań")

    st.write("🔽 Liczby z największym spadkiem:")
    for liczba, zmiana in trend_data[-10:]:
        st.write(f"Liczba {liczba}: {zmiana} porównań")
#Wykres trendów
    st.subheader("📈 Trend pojawiania się wybranej liczby w czasie")

    wybrana = st.number_input("📌 Wybierz liczbę (1–49)", min_value=1, max_value=49, value=6)
    bloków = 5  # możesz zmienić na 10 jeśli masz dużo danych
    dlugosc_bloku = len(wyniki) // bloków

    czestosci = []

    for i in range(bloków):
        start = i * dlugosc_bloku
        stop = start + dlugosc_bloku
        fragment = wyniki[start:stop]
        ile_razy = sum(wybrana in los for los in fragment)
        czestosci.append(ile_razy)

    fig, ax = plt.subplots()
    ax.plot(range(1, bloków+1), czestosci, marker='o', color='purple')
    ax.set_xticks(range(1, bloków+1))
    ax.set_xlabel("Blok czasowy (starsze → nowsze)")
    ax.set_ylabel("Liczba wystąpień")
    ax.set_title(f"Ilość wystąpień liczby {wybrana} w kolejnych blokach")
    st.pyplot(fig)

    st.subheader("🧊 Zimne liczby (najdawniej losowane)")
    
    ostatnie_wyst = {}
    for i in range(len(df)-1, -1, -1):
        for liczba in df.iloc[i]:
            if liczba not in ostatnie_wyst:
                ostatnie_wyst[liczba] = len(df) - i
    # Uzupełnienie brakujących liczb z zakresu 1–49
    for liczba in range(1, 50):
        if liczba not in ostatnie_wyst:
            ostatnie_wyst[liczba] = len(df)
    zimne_top10 = sorted(ostatnie_wyst.items(), key=lambda x: x[1], reverse=True)[:10]
    for liczba, dni in zimne_top10:
        st.write(f"Liczba {liczba}: nie była losowana od {dni} losowań")

    st.subheader("🔺 Najczęściej losowane trójki")
    trojki = Counter()
    for wiersz in wyniki:
        for trio in combinations(sorted(wiersz), 3):
            trojki[trio] += 1
    najczestsze_trojki = trojki.most_common(10)
    for (a, b, c), ile in najczestsze_trojki:
        st.write(f"Trójka {a}, {b}, {c}: {ile} razy")

    st.subheader("🔻 Najrzadziej losowane trójki (które wystąpiły)")
    rzadkie = [t for t in trojki.items() if t[1] > 0]
    rzadkie_sorted = sorted(rzadkie, key=lambda x: x[1])[:10]
    for (a, b, c), ile in rzadkie_sorted:
        st.write(f"Trójka {a}, {b}, {c}: {ile} razy")

    st.subheader("🎯 Propozycja 6 liczb")

    # 🔥 Zestaw z najczęstszych liczb
    top20 = [l for l, _ in licznik.most_common(20)]
    if len(top20) >= 6:
        zestaw_popularny = int(sorted(random.sample(top20, 6)))
        st.write(f"🔥 Zestaw z najczęstszych liczb: **{zestaw_popularny}**")

    # ❄️ Zestaw z zimnych liczb
    zimne_all = sorted(ostatnie_wyst.items(), key=lambda x: x[1], reverse=True)
    zimne_top20 = [l for l, _ in zimne_all[:20]]
    if len(zimne_top20) >= 6:
        zestaw_zimny = int(sorted(random.sample(zimne_top20, 6)))
        st.write(f"❄️ Zestaw z zimnych liczb: **{zestaw_zimny}**")

    st.subheader("📁 Pobierz dane")
    csv = df.to_csv(index=False)
    st.download_button("📥 CSV z wynikami", csv, file_name="wyniki_lotto.csv")

def main():
    init_db()  # utwórz tabelę, jeśli nie istnieje
    st.title("🎰 Lotto – analiza wyników z wielu źródeł")

    # Inicjalizacja stanu
    if "wyniki" not in st.session_state:
        st.session_state.wyniki = None

    zrodlo = st.radio("📡 Źródło danych:", ["API", "Scraper", "CSV z URL","Z bazy danych"])
    limit = st.slider("🔽 Liczba losowań do analizy (API/Scraper)", 50, 500, 200)

    if zrodlo == "CSV z URL":
        url_csv = STAŁY_CSV_URL
        st.info(f"Używany plik CSV: {url_csv}")
    else:
        url_csv = None

    if st.button("🔄 Pobierz i analizuj"):
        wyniki = None
        if zrodlo == "API":
            wyniki = pobierz_z_api(limit)
        elif zrodlo == "Scraper":
            wyniki = pobierz_z_html(strony=int(limit / 10))
        elif zrodlo == "CSV z URL":
            wyniki = pobierz_z_csv(url_csv)
        elif zrodlo == "Z bazy danych":
            wyniki = pobierz_wszystkie_wyniki()
            if wyniki:
                st.info(f"📦 Załadowano {len(wyniki)} zestawów z bazy danych.")

        if wyniki:
            st.session_state.wyniki = wyniki
            zapisz_wyniki_do_bazy(wyniki)
            st.success("💾 Wyniki zapisane do bazy danych.")
        else:
            st.error("❌ Nie udało się pobrać żadnych danych.")
            st.session_state.wyniki = None

    # Jeśli dane są dostępne — pokaż analizę
    if st.session_state.wyniki:
        analiza_lotto(st.session_state.wyniki)


if __name__ == "__main__":
    main()

    st.markdown("---")
    st.markdown("📌 **Autor:** Arnold Basiński  \n🔗 [github.com/ArnoldBasinski](https://github.com/ArnoldBasinski)  \n© 2025 Lotto Analyzer")

