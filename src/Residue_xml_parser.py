#!/Applications/anaconda3/envs/pisapy/bin/python3
"""
Code for parsing residue0.xml files in all child folders with depth 1 and saving data in a csv file and saving a .pdf plot.

  How to use
  ----------

First you need to have the residue0.xml file given by PDBePISA web server.

Then you can run the script with the following command :

    python Residue_xml_parser.py path/to/pisa_results/



"""

import os
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
import argparse
from src.Parse_Interfacetable import find_xml_files

def xmlresidue_parser(xml_file):
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()
    # List to store residue data
    residues_data = []

    # Iterate over RESIDUE1 and RESIDUE2 elements
    for residue_group in root.findall('.//RESIDUE1') + root.findall('.//RESIDUE2'):
        for residue in residue_group.findall('RESIDUE'):
            structure = residue.find('STRUCTURE').text.strip()
            chain = structure.split(':')[0]
            residue_number = ''.join(filter(str.isdigit, structure.split(':')[1]))
            amino_acid = structure.split(':')[1].split(residue_number)[0].strip()

            residue_data = {
                'CHAIN': chain,
                'RESIDUE': int(residue_number),
                'AMINOACID': amino_acid,
                'SOLVENTACCESSIBLEAREA': float(residue.find('SOLVENTACCESSIBLEAREA').text.strip()),
                'BURIEDSURFACEAREA': float(residue.find('BURIEDSURFACEAREA').text.strip()),
                'BURIEDSURFACEAREASCORE': float(residue.find('BURIEDSURFACEAREASCORE').text.strip()),
                'SOLVATIONENERGY': float(residue.find('SOLVATIONENERGY').text.strip())
            }
            residues_data.append(residue_data)

    # Convert to DataFrame
    df = pd.DataFrame(residues_data)
    max_residue_a = df[df['CHAIN'] == 'A']['RESIDUE'].max()
    df['CONTINUOUS_RESIDUE'] = df.apply(lambda row: row['RESIDUE'] if row['CHAIN'] == 'A' else row['RESIDUE'] + max_residue_a, axis=1)
    return df

def plot_residue_data(df):
    data = df.melt(id_vars=['CHAIN', 'RESIDUE', 'AMINOACID', 'CONTINUOUS_RESIDUE'], 
                   value_vars=['SOLVENTACCESSIBLEAREA', 'BURIEDSURFACEAREA', 'BURIEDSURFACEAREASCORE', 'SOLVATIONENERGY'],
                   var_name='Property', value_name='Value')
    
    scaler = StandardScaler()
    data['ScaledValue'] = data.groupby('Property')['Value'].transform(lambda x: scaler.fit_transform(x.values.reshape(-1, 1)).flatten())
    
    aspect_ratio = df['CONTINUOUS_RESIDUE'].max() / 100 * 3
    g = sns.catplot(data=data, x = 'CONTINUOUS_RESIDUE', y = 'Value', hue='ScaledValue', kind='strip', col='Property', palette='viridis', 
                    col_wrap=2, sharey=False, height=2, aspect=aspect_ratio, edgecolor='black', jitter=False)
    
    chain_b_start = df[df['CHAIN'] == 'B']['CONTINUOUS_RESIDUE'].min()-0.5

    for ax in g.axes.flat:
        ax.set_xticks(range(0, int(df['CONTINUOUS_RESIDUE'].max()), 50))
        ax.set_xlabel('Amino Acid')
        ax.axvline(chain_b_start, color='#624da0', linestyle='--')
        ax.text(chain_b_start / 2, ax.get_ylim()[1] * 0.95, 'Binder', horizontalalignment='center', color='#624da0', fontsize=10)
        ax.text(chain_b_start + (df['CONTINUOUS_RESIDUE'].max() - chain_b_start) / 2, ax.get_ylim()[1] * 0.95, 'Target', horizontalalignment='center', color='#624da0', fontsize=10)
    
    

    titles = {
        'SOLVENTACCESSIBLEAREA': 'Solvent Accessible Area',
        'BURIEDSURFACEAREA': 'Buried Surface Area',
        'BURIEDSURFACEAREASCORE': 'Buried Surface Area Score',
        'SOLVATIONENERGY': 'Solvation Energy'
    }
    g.set_titles(col_template="{col_name}", row_template="{row_name}")
    for ax in g.axes.flat:
        col_name = ax.get_title().split(' = ')[-1]
        ax.set_title(titles.get(col_name, col_name), size=14, color='#2b215f', fontweight='bold')

    min_solvation_energy = df[df['CHAIN'] == 'A'].nsmallest(1, 'SOLVATIONENERGY').iloc[0]
    min_residue = min_solvation_energy['CONTINUOUS_RESIDUE']
    min_value = min_solvation_energy['SOLVATIONENERGY']
    min_amino_acid = min_solvation_energy['AMINOACID']
    min_residue_number = min_solvation_energy['RESIDUE']

    max_solvation_energy = df[df['CHAIN'] == 'A'].nlargest(1, 'SOLVATIONENERGY').iloc[0]
    max_residue = max_solvation_energy['CONTINUOUS_RESIDUE']
    max_value = max_solvation_energy['SOLVATIONENERGY']
    max_amino_acid = max_solvation_energy['AMINOACID']
    max_residue_number = max_solvation_energy['RESIDUE']

    for ax in g.axes.flat:
        if ax.get_title() == 'Solvation Energy':
            ax.text(min_residue-2, min_value, f'{min_amino_acid}{min_residue_number} : ΔG = {round(min_value, 2)} kcal/M', color='#f8991d', fontsize=8, ha='right')
            ax.text(max_residue-2, max_value, f'{max_amino_acid}{max_residue_number} : ΔG = {round(max_value, 2)} kcal/M', color='#f8991d', fontsize=8, ha='right')
    return g

if __name__ == '__main__':
    PARSER = argparse.ArgumentParser()

    PARSER.add_argument("root_dir", help="the root directory to search for residue0.xml files", type=str)

    ARGS = PARSER.parse_args()

    ROOT_DIR = ARGS.root_dir

    xml_files = find_xml_files(ROOT_DIR, filename="residue0.xml")

    for xml_file in xml_files:
        df = xmlresidue_parser(xml_file)
        output_file = os.path.join(os.path.dirname(xml_file), "ResidueTable.csv")
        df.to_csv(output_file)
        plot_residue_data(df)
        plt.savefig(os.path.join(os.path.dirname(xml_file), "ResiduePlot.pdf"))
        plt.close


