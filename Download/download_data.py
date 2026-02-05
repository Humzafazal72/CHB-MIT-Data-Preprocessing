import os
import json
import requests
import argparse
from tqdm import tqdm
from typing import Literal
from bs4 import BeautifulSoup

ref_link = "https://physionet.org/content/chbmit/1.0.0/{patient_id}/{file_name}"

def download_file(url: str, filepath: str, desc: str = "Downloading"):
    """Download a file with progress bar"""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    # Get total file size from headers
    total_size = int(response.headers.get('content-length', 0))
    
    # Create progress bar for this specific file
    with open(filepath, 'wb') as f, tqdm(
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
        desc=desc,
        leave=False  # Don't leave the bar after completion
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))


def begin_downloads(type_: Literal["preictal","interictal"]):
    os.makedirs(f"{type_}/", exist_ok=True)
    existing_files = os.listdir(f"{type_}/")
    
    with open(f"./{type_}.json", 'r') as file:
        data = json.load(file)
    
    for d in tqdm(data, desc=f"Downloading {type_}"):
        f_name = d['File Name']
        
        if f_name in existing_files:
            continue
            
        patient_id = f_name.split("_")[0] if "17" not in f_name else "chb17"
        
        try:
            response = requests.get(ref_link.format(patient_id=patient_id, file_name=f_name))
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            div = soup.find("div", class_="text-center")    
            link_tag = div.find("a")
            partial_link = link_tag["href"]
            complete_link = "https://physionet.org/" + partial_link
            
            download_file(complete_link, f"{type_}/{f_name}", desc=f"📥 {f_name}")

        except Exception as e:
            with open(f"failed_{type_}.txt", 'a') as file:
                file.write(f_name+"\n") 
            print(f"Error downloading {f_name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--class_', type=str, 
                       choices=['preictal','interictal'], 
                       help='Choose the class i.e. preictal or interictal',
                       default="interictal")
    args = parser.parse_args()
    begin_downloads(args.class_)