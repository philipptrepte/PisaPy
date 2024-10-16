#!/Applications/anaconda3/envs/pisapy/bin/python3
"""
Code to automatically run PDBePISA web server on pdb files and downloading the
generated xml files.

  How to use
  ----------

First you need to have the python packages selenium, halo and argparse installed 
and the PisaAuto_id.py script, you also need the pdb files on witch you want to 
run pisa.

Then you can run the script with the following command :

    python PisaAuto_file.py path_to_pdb_files_folder/


Note that right now it's made for firefox browser but adding other browsers 
isn't hard to implement (ex: driver = webdriver.Chrome() for chrome).
Also note that only the interface table, the residues interaction and interfacing 
residues xml files are downloaded. 
hard

  Author
  ------
    Hocine Meraouna

"""

import time
import os
import sys
import pandas as pd
from os import listdir
from os.path import isfile
import argparse
import matplotlib.pyplot as plt
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from halo import Halo
import PisaAuto_id as pisa
from Parse_Interfacetable import parse_interface, find_xml_files
from Pisa_xml_parser import create_df, interfacetable_parse
from Residue_xml_parser import xmlresidue_parser, plot_residue_data

def check_exists_by_name(name, driver):
    """
    The function to check if an element is present on the webdriver.

    Parameters
    ----------
    driver : selenium webdriver
    name : string
        the name of the element

    Returns
    -------
    boolean
    """
    try:
        driver.find_element(By.NAME, name)
    except NoSuchElementException:
        return False
    return True

def launch_pdb_file(driver, pdb_file):
    """
    The function to run pisa web service on the pdb file.

    Parameters
    ----------
    driver : selenium webdriver
        given by the function PisaAuto_id.start()
    pdb_file : string
        corresponding to the pdb given by the user

    Returns
    -------
    selenium webdriver
    """
    print("2- Uploading "+pdb_file+" :")

    spinner = Halo(text='Uploading pdb file', spinner='dots')
    spinner.start()

    driver.find_elements(By.NAME, 'radio_source')[1].click()

    time.sleep(6)

    driver.find_element(By.NAME, "file_upload").send_keys(os.getcwd()+"/"+pdb_file)

    time.sleep(5)

    driver.find_element(By.NAME, "btn_upload").click()

    while(not check_exists_by_name('btn_submit_interfaces', driver)):
        pass

    driver.find_element(By.NAME, "btn_submit_interfaces").click()

    spinner.stop()

    print("Done")

    print("3- Running PISA on "+pdb_file+" :")

    spinner = Halo(text='Running Pisa', spinner='dots')
    spinner.start()

    time.sleep(4)

    if driver.find_element(By.CLASS_NAME, "phead").text.startswith("No"):

        spinner.stop()
        
        print('No Contacts found')

        return driver, False

    else:
        while(not check_exists_by_name('downloadXML', driver)):
            pass

        time.sleep(4)

        spinner.stop()

        return driver, True


if __name__ == '__main__':

    PARSER = argparse.ArgumentParser()

    PARSER.add_argument("pdb_path", help="the path of the pdb files directory", type=str)

    ARGS = PARSER.parse_args()

    PDB_PATH = ARGS.pdb_path
    ROOT_DIR = os.path.abspath(ARGS.pdb_path)

    PDB_FILES = sorted([PDB_PATH+f for f in listdir(PDB_PATH) 
        if ((isfile(PDB_PATH+f)) and 
            (f.split(".")[-1] == "pdb"))], key=str.lower)

    for i, file in enumerate(PDB_FILES):
        print("## pdb file "+str(i+1)+"/"+str(len(PDB_FILES)))
        driver = pisa.start()
        driver, boo = launch_pdb_file(driver, file)
        if boo:
            pisa.download_xmls(driver, file.split('/')[-1], path=PDB_PATH)
        driver.quit()
    
    xml_files = find_xml_files(ROOT_DIR)

    print("5-Parsing InterfaceTable.xml files")
    for xml_file in xml_files:
        df = pd.DataFrame.from_dict(parse_interface(xml_file))
        output_file = os.path.join(os.path.dirname(xml_file), "InterfaceTable.csv")
        df.to_csv(output_file)

    for xml_file in xml_files:
        print(f"Processing {xml_file}")
        df = create_df(interfacetable_parse(xml_file))
        output_file = os.path.join(os.path.dirname(xml_file), "InteractionSheet.csv")
        df.to_csv(output_file)
    print("Done")

    print("6-Parsing Residue0.xml files")
    residue_xml_files = find_xml_files(ROOT_DIR, filename="residue0.xml")

    for xml_file in residue_xml_files:
        df = xmlresidue_parser(xml_file)
        output_file = os.path.join(os.path.dirname(xml_file), "ResidueTable.csv")
        df.to_csv(output_file)
        plot_residue_data(df)
        plt.savefig(os.path.join(os.path.dirname(xml_file), "ResiduePlot.pdf"))
        plt.close
    print("Done")
