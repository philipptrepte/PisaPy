#!/Applications/anaconda3/envs/pisapy/bin/python
"""
Code to parse interfacetable.xml and generate a csv file with the xml file data.

  How to use
  ----------
First you need to have the python packages pandas and argparse, and the interfacetable.xml
and each hydrogenbond.xml files given by pisa web server.

Then you can run the script with the following command :
    python Parse_Interfacetable.py path/to/pisa_results/

  Author
  ------
    Hocine Meraouna
"""

import argparse
import pandas as pd
import os.path

def find_chain(xml_file):
    """
    """
    chains = ['/', '/']
    with open(xml_file, "r") as f_xml:
        for line in f_xml :
            if line.startswith('<STRUCTURE1>'):
                chains[0] = line.split('>')[1].strip()[0]
            if line.startswith('<STRUCTURE2>'):
                chains[1] = line.split('>')[1].strip()[0]
                return chains
    return chains

def get_surf(xml_file):
    """
    """
    s = 1
    with open(xml_file, 'r') as f_xml:
        for line in f_xml:
            if line.startswith('<STRUCTURE2>'):
                s = 2
            if (line.startswith('<INTERFACEAREA>')) and (s == 1):
                x1 = float(line.split('>')[1].split('<')[0])
            elif (line.startswith('<INTERFACEAREA>')) and (s == 2):
                x2 = float(line.split('>')[1].split('<')[0])
    return ((x1+x2)/2)

def parse_interface(xml_file):
    """
    """
    dico = {'Chain 1': [], 'Nres 1': [], 'SolvAccessSurface 1': [], 
        'Chain 2': [], 'Nres 2': [], 'SolvAccessSurface 2': [], 
        'ΔiGkcal/mol': [], 'ΔiGP-value': [], 
        'Nhb': [], 'Nsb': [], 'Nds': [], 'CSS': [], 'InterfaceSurface': []}

    path = '/'.join(xml_file.split('/')[:-1])

    with open(xml_file, 'r') as f_xml:
        for line in f_xml :
            if line.startswith('<INTERFACENO>'):
                if os.path.isfile(path+"/hydrogenbond"+str(int(line.split('>')[1].split('<')[0])-1)+".xml"):
                    dico['Chain 1'].append(find_chain(path+"/hydrogenbond"+str(int(line.split('>')[1].split('<')[0])-1)+".xml")[0])
                    dico['Chain 2'].append(find_chain(path+"/hydrogenbond"+str(int(line.split('>')[1].split('<')[0])-1)+".xml")[1])
                elif os.path.isfile(path+"/saltbridge"+str(int(line.split('>')[1].split('<')[0])-1)+".xml"):
                    dico['Chain 1'].append(find_chain(path+"/saltbridge"+str(int(line.split('>')[1].split('<')[0])-1)+".xml")[0])
                    dico['Chain 2'].append(find_chain(path+"/saltbridge"+str(int(line.split('>')[1].split('<')[0])-1)+".xml")[1])
                else:
                    dico['Chain 1'].append('?')
                    dico['Chain 2'].append('?')
                if os.path.isfile(path+"/interfacesummary"+str(int(line.split('>')[1].split('<')[0])-1)+".xml"):
                    dico['InterfaceSurface'].append(get_surf(path+"/interfacesummary"+str(int(line.split('>')[1].split('<')[0])-1)+".xml"))

            if line.startswith('<INTERFACENRESIDUES1>'):
                dico['Nres 1'].append(int(line.split('>')[1].split('<')[0]))

            if line.startswith("<TOTALSURFACEAREA1>"):
                dico['SolvAccessSurface 1'].append(float(line.split('>')[1].split('<')[0]))
        
            if line.startswith('<INTERFACENRESIDUES2>'):
                dico['Nres 2'].append(int(line.split('>')[1].split('<')[0]))

            if line.startswith("<TOTALSURFACEAREA2>"):
                dico['SolvAccessSurface 2'].append(float(line.split('>')[1].split('<')[0]))

            if line.startswith("<INTERFACEAREA>"):
                dico['ΔiGkcal/mol'].append(float(line.split('>')[1].split('<')[0]))
        
            if line.startswith("<INTERFACEDELTAGPVALUE>"):
                dico['ΔiGP-value'].append(float(line.split('>')[1].split('<')[0]))
        
            if line.startswith("<INTERFACENHBONDS>"):
                dico['Nhb'].append(int(line.split('>')[1].split('<')[0]))
        
            if line.startswith("<INTERFACENSALTBRIDGES>"):
                dico['Nsb'].append(int(line.split('>')[1].split('<')[0]))
        
            if line.startswith("<INTERFACENDISULFIDEBONDS>"):
                dico['Nds'].append(int(line.split('>')[1].split('<')[0]))
        
            if line.startswith("<INTERFACECSS>"):
                dico['CSS'].append(float(line.split('>')[1].split('<')[0]))

    # Ensure all lists in the dictionary have the same length
    max_length = max(len(lst) for lst in dico.values())
    for key, lst in dico.items():
        if len(lst) < max_length:
            dico[key] = lst + [None] * (max_length - len(lst))

    return dico

def find_xml_files(root_dir, filename="interfacetable.xml"):
    xml_files = []
    for root, dirs, files in os.walk(root_dir):
        # Only go one level deep
        if root.count(os.sep) - root_dir.count(os.sep) < 2:
            for file in files:
                if file == filename:
                    xml_files.append(os.path.join(root, file))
    return xml_files

if __name__ == '__main__':

    PARSER = argparse.ArgumentParser()

    PARSER.add_argument("root_dir", help="the root directory to search for interfacetable.xml files", type=str)

    ARGS = PARSER.parse_args()

    ROOT_DIR = ARGS.root_dir

    xml_files = find_xml_files(ROOT_DIR)

    for xml_file in xml_files:
        df = pd.DataFrame.from_dict(parse_interface(xml_file))
        output_file = os.path.join(os.path.dirname(xml_file), "InterfaceTable.csv")
        df.to_csv(output_file)
