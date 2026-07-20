import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from tkinter import Tk, Label, Entry, Button, Radiobutton, StringVar

# ===================== Global configuration and folder initialization =====================
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题

# Define the path of the data root folder (make sure that the folder contains the CSV files to be analyzed)
folder_path = 'data'
# Define the root saving path for the analysis result images and concatenate it under the "data" folder.
image_folder_path = os.path.join(folder_path, 'Individuals Chart')
# If the image save folder does not exist, create this folder
if not os.path.exists(image_folder_path):
    os.makedirs(image_folder_path)


# ===================== Data processing function =====================
def process_data(data, h_method, h):
    """
    Calculate the value of H, which represents the width of the control limit
    :param data
    :param h_method
    :param h
    :return
    """
    target = data[0]  

    # MR_bar_h and d2
    if h_method == 'mean':
        # method 1: mean
        MR_bar_h = np.mean(np.abs(np.diff(data)))
        d2_2_h = 1.128  
    elif h_method == 'median':
        # method 2: med
        MR_bar_h = np.median(np.abs(np.diff(data)))
        d2_2_h = 0.954  
    elif h_method == 'target_percent':
        # method 3: target/100
        MR_bar_h = target / 100
        d2_2_h = 1  

    sigma_h = MR_bar_h / d2_2_h  
    H = round(h * sigma_h, 2) 
    return H


# ===================== Drawing and image saving function =====================
def plot_original_data(data, column_name, file_name, H, h, h_method):
    """
    :param data
    :param column_name
    :param file_name
    :param H
    :param h
    :param h_method
    :return
    """
    plt.figure(figsize=(9, 6))
    x_values = range(1, len(data) + 1)  #

    plt.plot(x_values, data, marker='o', linestyle='-', color='b', label='Actual Data')

    # UCL LCL
    ucl = round(data[0] + H, 2)
    lcl = round(data[0] - H, 2)

    plt.axhline(ucl, color='red', linestyle='-', label='UCL')
    plt.axhline(lcl, color='red', linestyle='-', label='LCL')

    plt.text(35, ucl - 0.08, f'UCL={ucl}', color='red')
    plt.text(35, lcl - 0.08, f'LCL={lcl}', color='red')

    plt.title(f'Individuals Chart of {column_name}')  
    plt.xlabel('Fraction') 
    plt.ylabel(f'{column_name} (cGy)')
    plt.grid(True) 

    xticks_positions = [1, 5, 10, 15, 20, 25, 30]
    plt.xticks(xticks_positions)

    file_base_name = os.path.splitext(file_name)[0]
    file_specific_folder_path = os.path.join(image_folder_path, f"{file_base_name}_IndividualsChart")
    if not os.path.exists(file_specific_folder_path):
        os.makedirs(file_specific_folder_path)

    #image_name = f"{file_base_name},{column_name},h={h},h_method={h_method}.jpg"
    #full_image_path = os.path.join(file_specific_folder_path, image_name)
   # plt.savefig(full_image_path, format='jpg', bbox_inches='tight', dpi=300)

    image_name = f"{column_name},h={h},h_method={h_method}.pdf"
    full_image_path = os.path.join(file_specific_folder_path, image_name)
    plt.savefig(full_image_path, format='pdf', bbox_inches='tight')
    plt.close()


# ===================== Batch analysis execution function  =====================
def run_analysis(h, h_method):
    """
    Iterate through all CSV files in the "data" folder
    """
    for file_name in os.listdir(folder_path):
        #  .csv file
        if not file_name.lower().endswith('.csv'):
            continue

        # Skip temporary files
        if file_name.startswith('~$'):
            continue

        file_path = os.path.join(folder_path, file_name)

        try:
            # Read .CSV
            data_df = pd.read_csv(file_path, encoding='utf-8-sig')

            for column_name in data_df.columns:
                try:
                    # Clean the data: Remove null values and convert to numerical values
                    data = data_df[column_name].dropna().values.astype(float)
                    if len(data) < 1:
                        continue

                    H = process_data(data, h_method, h)
                    plot_original_data(data, column_name, file_name, H, h, h_method)
                except:
                    # A column is non-numeric, skipping it.
                    continue

        except Exception as e:
            print(f"Processing failed:{file_name}，error:{str(e)}")


# ===================== GUI interface and main program entry point =====================
def main():
    root = Tk()
    root.title("Input the value of h and the calculation method of sigma.")

    Label(root, text="Please enter h value:").grid(row=0)
    h_entry = Entry(root)
    h_entry.grid(row=0, column=1)

    h_method_var = StringVar(value=None)
    Label(root, text="Please select sigma calculation method for H:").grid(row=2)
    Radiobutton(root, text="Mean", variable=h_method_var, value='mean').grid(row=3, column=0)
    Radiobutton(root, text="Median", variable=h_method_var, value='median').grid(row=3, column=1)
    Radiobutton(root, text="Target/100", variable=h_method_var, value='target_percent').grid(row=3, column=2)

    def on_submit():
        try:
            h = float(h_entry.get())
            h_method = h_method_var.get()
            if h_method:
                run_analysis(h, h_method)
                root.destroy()
            else:
                print("Please select a calculation method for H.")
        except ValueError:
            print("Please enter a valid number!")

    Button(root, text="OK", command=on_submit).grid(row=6, column=1)
    root.mainloop()


if __name__ == "__main__":
    main()
