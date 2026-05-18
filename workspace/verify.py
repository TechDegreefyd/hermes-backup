from bs4 import BeautifulSoup
import re

with open('/workspace/Degreefyd_Final_Master_White.html', 'r') as f:
    soup = BeautifulSoup(f, 'html.parser')

mtd_header = soup.find('h3', text=re.compile('Overall Summary \(MTD\)'))
if mtd_header:
    # Next element is the kpi band
    kpi_band = mtd_header.find_next_sibling('div', class_='kpi-band')
    for kc in kpi_band.find_all('div', class_='kc'):
        lbl = kc.find('div', class_='kc-lbl').text
        val = kc.find('div', class_='kc-val').text
        print(f"MTD {lbl}: {val}")
