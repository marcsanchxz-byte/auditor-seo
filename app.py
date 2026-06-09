import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json

st.set_page_config(page_title="Auditor SEO Local Express", layout="centered")

st.title("🛡️ Auditor Real SEO Local")
st.subheader("Pega los enlaces y obtén tus porcentajes para la plantilla")

# Formulario de entrada
with st.form("auditoria_form"):
    url_maps = st.text_input("1. URL de Google Maps de la ficha:")
    url_web = st.text_input("2. URL de la página Web del negocio (ej: https://web.com):")
    enviar = st.form_submit_button("Auditar Negocio")

if enviar:
    if not url_maps or not url_web:
        st.warning("Por favor, introduce ambas URLs para poder calcular todo el informe.")
    else:
        with st.spinner("Rastreando y calculando baremos en tiempo real..."):
            if not url_web.startswith("http"):
                url_web = "https://" + url_web
                
            score_ficha = 100
            score_servicios = 50  
            score_reputacion = 80
            score_visuales = 50
            score_web = 20
            
            nota_estrellas = 4.0
            tiene_schema = False
            tiene_sitemap = False
            tiene_canonical = False

            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

            try:
                res_maps = requests.get(url_maps, headers=headers, timeout=12)
                html_maps = res_maps.text
                match_estrellas = re.search(r'(\d[.,]\d)\s*stars', html_maps) or re.search(r'(\d[.,]\d)\s*estrellas', html_maps)
                if match_estrellas:
                    nota_estrellas = float(match_estrellas.group(1).replace(",", "."))
                    score_reputacion = int((nota_estrellas / 5.0) * 100)
                    score_reputacion = max(0, score_reputacion - 20)
            except:
                pass

            try:
                res_web = requests.get(url_web, headers=headers, timeout=10)
                html_web = res_web.text
                soup = BeautifulSoup(html_web, "html.parser")
                
                scripts_json = soup.find_all("script", type="application/ld+json")
                for s in scripts_json:
                    try:
                        data = json.loads(s.string)
                        if isinstance(data, dict) and (data.get("@type") == "LocalBusiness" or "@graph" in data):
                            tiene_schema = True
                        elif isinstance(data, list):
                            for item in data:
                                if item.get("@type") == "LocalBusiness":
                                    tiene_schema = True
                    except:
                        continue
                
                if soup.find("link", rel="canonical"):
                    tiene_canonical = True
                    
                if tiene_schema: score_web += 40
                if tiene_canonical: score_web += 15
                
                dominio_base = url_web.split("//")[-1].split("/")[0]
                res_robots = requests.get(f"https://{dominio_base}/robots.txt", headers=headers, timeout=5)
                if "sitemap" in res_robots.text.lower():
                    tiene_sitemap = True
                    score_web += 15
            except:
                pass

            nota_final = int(
                (score_ficha * 0.20) + 
                (score_servicios * 0.20) + 
                (score_reputacion * 0.25) + 
                (score_visuales * 0.15) + 
                (score_web * 0.20)
            )

            st.markdown("---")
            st.header("📋 Datos Mascados para tu Plantilla")
            st.metric(label="📊 SCORE GENERAL CALCULADO", value=f"{nota_final} / 100")
            
            texto_copiar = f"""
📌 DATOS PARA LA CALCULADORA:
• Ficha Principal: {score_ficha}%
• Servicios y Señales: {score_servicios}%
• Reputación: {score_reputacion}% (Estrellas detectadas: {nota_estrellas}⭐)
• Contenido Visual: {score_visuales}%
• Web y Schema: {score_web}%

🚨 BRECHAS DETECTADAS:
- Schema LocalBusiness: {"✅ Detectado" if tiene_schema else "❌ FALTANTE (Prioridad Alta)"}
- Etiqueta Canonical: {"✅ Detectada" if tiene_canonical else "❌ FALTANTE"}
- Sitemap XML en Robots: {"✅ Indexado" if tiene_sitemap else "❌ NO DETECTADO"}
            """
            st.text_area("Copia este bloque y llévatelo a tu Excel o Notion:", texto_copiar, height=250)
