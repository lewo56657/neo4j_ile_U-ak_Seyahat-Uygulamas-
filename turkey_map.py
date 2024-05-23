
import geopandas as gpd
import matplotlib.pyplot as plt
from neo4j import GraphDatabase
from shapely.geometry import Point
import tkinter as tk
from tkinter import simpledialog, messagebox
from matplotlib.animation import FuncAnimation
import numpy as np
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# Neo4j bağlantısı
url = "bolt://localhost:7687"
kullanici_adi = "neo4j"
sifre = "neo4j.5656"

# Neo4j sorgusu
query = """
MATCH (city:City)
RETURN city.name AS name, city.latitude AS latitude, city.longitude AS longitude
"""

# Neo4j'ye bağlanma ve veri alımı
driver = GraphDatabase.driver(url, auth=(kullanici_adi, sifre))
with driver.session() as session:
    result = session.run(query)
    city_data = [(record['name'], record['latitude'], record['longitude']) for record in result]

# Türkiye haritasını yükleme
turkey = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
turkey = turkey[turkey.name == "Turkey"]

# Şehir koordinatlarını GeoDataFrame'e dönüştürme
geometry = [Point(lon, lat) for _, lat, lon in city_data]
city_gdf = gpd.GeoDataFrame(city_data, geometry=geometry, columns=['City', 'Latitude', 'Longitude'])

def draw_map(city_name1, city_name2, date1, date2):
    fig, ax = plt.subplots(figsize=(10, 10))
    turkey.plot(ax=ax, color='lightgrey')
    city_gdf.plot(ax=ax, marker='o', color='red', markersize=50)
    
    # Şehir isimlerini noktaların üzerine yazma
    for idx, row in city_gdf.iterrows():
        ax.text(row.geometry.x, row.geometry.y, row['City'], fontsize=11, ha='right')

    ax.set_title('Türkiye Haritası')
    ax.set_xlabel('Boylam')
    ax.set_ylabel('Enlem')

    # Kalkış ve varış noktalarının koordinatlarını bulma
    start_point = city_gdf[city_gdf['City'] == city_name1].geometry.values[0]
    end_point = city_gdf[city_gdf['City'] == city_name2].geometry.values[0]

    # Çizgi için interpolasyon yapma
    xdata = np.linspace(start_point.x, end_point.x, 50)  # Daha hızlı animasyon için adım sayısını azalt
    ydata = np.linspace(start_point.y, end_point.y, 50)

    # Sağ alt köşeye metin ekleme
    text = f"Kalkış: {city_name1}\nVarış: {city_name2}\nTarih 1: {date1}\nTarih 2: {date2}"
    ax.text(0.95, 0.05, text, fontsize=12, ha='right', va='bottom', transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))

    line, = ax.plot([], [], 'b--', linewidth=2)

    # Uçak ikonu yükleme
    plane_img = plt.imread("ucak3.png")
    imagebox = OffsetImage(plane_img, zoom=0.09)  # Zoom değerini ayarlayarak ikon boyutunu değiştirebilirsiniz
    plane = AnnotationBbox(imagebox, (start_point.x, start_point.y), frameon=False)

    ax.add_artist(plane)

    def init():
        line.set_data([], [])
        plane.xy = (start_point.x, start_point.y)
        return line, plane

    def animate(i):
        line.set_data(xdata[:i+1], ydata[:i+1])
        plane.xy = (xdata[i], ydata[i])
        return line, plane

    ani = FuncAnimation(fig, animate, frames=len(xdata), init_func=init, blit=True, repeat=False, interval=100)  # interval parametresi hız kontrolü sağlar
    plt.show()

def get_inputs():
    root = tk.Tk()
    root.withdraw()  # Tkinter penceresini gizle

    city_name1 = simpledialog.askstring("Input", "Kalkış Noktası:")
    city_name2 = simpledialog.askstring("Input", "Varış Noktası:")
    date1 = simpledialog.askstring("Input", "Tarih 1 (gg/aa/yyyy):")
    date2 = simpledialog.askstring("Input", "Tarih 2 (gg/aa/yyyy):")

    return city_name1, city_name2, date1, date2

def check_travel_exists(city_name1, city_name2):
    travel_query = """
    MATCH (start:City {name: $city_name1})-[r:Seyahat]->(end:City {name: $city_name2})
    RETURN count(r) AS travel_exists
    """
    with driver.session() as session:
        result = session.run(travel_query, city_name1=city_name1, city_name2=city_name2)
        travel_exists = result.single()['travel_exists']
        return travel_exists > 0

city_name1, city_name2, date1, date2 = get_inputs()

if check_travel_exists(city_name1, city_name2):
    draw_map(city_name1, city_name2, date1, date2)
else:
    messagebox.showinfo("Uyarı", "Sefer bulunamadı")

driver.close()



