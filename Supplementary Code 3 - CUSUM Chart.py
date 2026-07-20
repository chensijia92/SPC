import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from tkinter import Tk, Label, Entry, Button, Radiobutton, StringVar

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# Specify the folder path
folder_path = 'data'
ROOT_OUTPUT_FOLDER = os.path.join(folder_path, "CUSUM Chart")
# The name of the target column that needs to be analyzed
TARGET_COLUMNS = ['GTVp_Dmean', 'GTVn_Dmean', 'Parotid_L_Dmean', 'Parotid_R_Dmean', 'Larynx_Dmean']


# The function for processing each column of data
def process_data(data, h_method, k_method, h, k):
    target = data[0]
    # Calculate the sigma of H
    if h_method == 'mean':
        MR_bar_h = np.mean(np.abs(np.diff(data)))
        d2_2_h = 1.128
    elif h_method == 'median':
        MR_bar_h = np.median(np.abs(np.diff(data)))
        d2_2_h = 0.954
    elif h_method == 'target_percent':
        MR_bar_h = target / 100
        d2_2_h = 1
    sigma_h = MR_bar_h / d2_2_h

    # Calculate the sigma of K
    if k_method == 'mean':
        MR_bar_k = np.mean(np.abs(np.diff(data)))
        d2_2_k = 1.128
    elif k_method == 'median':
        MR_bar_k = np.median(np.abs(np.diff(data)))
        d2_2_k = 0.954
    elif k_method == 'target_percent':
        MR_bar_k = target / 100
        d2_2_k = 1
    sigma_k = MR_bar_k / d2_2_k

    H = round(h * sigma_h, 2)
    K = round(k * sigma_k, 2)

    cumulative_sum1 = 0
    cumulative_sum2 = 0
    data1 = []
    data2 = []
    for value in data:
        deviation1 = value - (target + K) + cumulative_sum1
        cumulative_sum1 = deviation1 if deviation1 > 0 else 0
        data1.append(cumulative_sum1)

        deviation2 = (target - K) - value + cumulative_sum2
        cumulative_sum2 = deviation2 if deviation2 > 0 else 0
        data2.append(-cumulative_sum2)
    return data1, data2, H


# The function for drawing CUSUM charts
def plot_cumsum(data1, data2, H, column_name):
    plt.figure(figsize=(9, 6))
    x_values = range(1, len(data1) + 1)
    plt.plot(x_values, data1, marker='o', linestyle='-', color='b')
    plt.plot(x_values, data2, marker='s', linestyle='-', color='b')

 #   for i, (x1, x2) in enumerate(zip(data1, data2)):
#        if x1 > H or x1 < -H:
 #           plt.plot(i + 1, x1, 'ro', label='Out of Control' if i == 0 else "")
 #       if x2 > H or x2 < -H:
  #          plt.plot(i + 1, x2, 'rs', label='Out of Control' if i == 0 else "")

    plt.text(35, H - 0.08, f'UCL={H}', color='red')
    plt.text(35, -H - 0.08, f'LCL={-H}', color='red')
    plt.axhline(H, color='red', linewidth=1, linestyle='-')
    plt.axhline(-H, color='red', linewidth=1, linestyle='-')
    plt.title(f'CUSUM Chart of {column_name} ')
    plt.xlabel('Fraction')
    plt.ylabel('Cumulative Sum')
    plt.grid(True)
    xticks_positions = [1, 5, 10, 15, 20, 25, 30]
    plt.xticks(xticks_positions)
    return plt


# Over-limit detection and marking function
def check_control_status(data1, data2, H):
    over_ucl = np.array(data1) > H
    over_lcl = np.array(data2) < -H

    # Determine if there is an excessive limit between two consecutive points
    has_ucl_continuous = any(over_ucl[i] and over_ucl[i + 1] for i in range(len(over_ucl) - 1))
    has_lcl_continuous = any(over_lcl[i] and over_lcl[i + 1] for i in range(len(over_lcl) - 1))

    # Determine the marking symbol
    if has_ucl_continuous and has_lcl_continuous:
        mark = "X" #Both the upper and lower limits exceed.
    elif has_ucl_continuous:
        mark = "+"
    elif has_lcl_continuous:
        mark = "-"
    else:
        mark = "*" #All within the control limits.


    # Only when the value is not zero, the first over-limit point will be searched for. If it is marked as zero, it will be fixed as *.
    first_over_idx = "*"
    if mark != "0":
        for i in range(len(over_ucl)):
            if over_ucl[i] or over_lcl[i]:
                first_over_idx = i + 1
                break
    return mark, first_over_idx


# -------------------------- Statistical table generation function --------------------------
def generate_stat_table(stats_data, h, k, h_method, k_method):

    patients = list(stats_data.keys())
    patient_nos = [str(i + 1) for i in range(len(patients))]  # 患者序号转字符串

    temp_data = {
        'Patient No': patient_nos,
        'Patient Name': patients
    }
    for col in TARGET_COLUMNS:
        col_marks = []
        col_stages = []
        for p in patients:
            if col not in stats_data[p]:
                col_marks.append("")
                col_stages.append("")
            else:
                col_marks.append(stats_data[p][col]['mark'])
                col_stages.append(str(stats_data[p][col]['stage']))
        temp_data[col] = col_marks
        temp_data[f'{col}_Fraction.'] = col_stages

    temp_df = pd.DataFrame(temp_data)
    transposed_df = temp_df.set_index('Patient No').T  # 转置：行变列，列变行

    transposed_df.index.name = 'Patient No.'

    transposed_df.columns.name = None

    file_name = f'CUSUM Trend_h={h}_k={k}_hm={h_method}_km={k_method}.xlsx'
    save_path = os.path.join(ROOT_OUTPUT_FOLDER, file_name)
    transposed_df.to_excel(save_path, index=True)
    print(f" The transposed statistical table has been saved:{file_name}")
    return transposed_df


# Run the analysis function
def run_analysis(h, k, h_method, k_method):
    os.makedirs(ROOT_OUTPUT_FOLDER, exist_ok=True)

    stats_data = {}
    #  Only read the CSV file
    patient_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.csv')]

    for file_name in patient_files:
        patient_name = os.path.splitext(file_name)[0]
        stats_data[patient_name] = {}
        file_path = os.path.join(folder_path, file_name)

        patient_output_folder = os.path.join(ROOT_OUTPUT_FOLDER, f"{patient_name}_CUSUMChart")
        os.makedirs(patient_output_folder, exist_ok=True)

        #  读Read CSV (UTF-8)
        data_df = pd.read_csv(file_path, encoding='utf-8-sig')


        images_folder = os.path.join(folder_path, patient_name)
        if not os.path.exists(images_folder):
            os.makedirs(images_folder)

        # Only process the target column
        for col in TARGET_COLUMNS:
            if col not in data_df.columns:
                continue
            try:
                data = data_df[col].dropna().values.astype(float)
                if len(data) < 2:
                    continue
                # CUSUM chart
                data1, data2, H = process_data(data, h_method, k_method, h, k)
                # Save the drawing
                plt_obj = plot_cumsum(data1, data2, H, col)

                #img_name = f"{col}_h{h}_k{k}.jpg"
                #plt_obj.savefig(os.path.join(images_folder, img_name), bbox_inches='tight', dpi=300)

                img_name = f"{col}_h{h}_k{k}.pdf"
                plt_obj.savefig(
                    os.path.join(patient_output_folder, img_name),
                    format='pdf',
                    bbox_inches='tight'
                )

                plt_obj.close()
                # Detecting over-limit conditions
                mark, stage = check_control_status(data1, data2, H)
                stats_data[patient_name][col] = {'mark': mark, 'stage': stage}
            except Exception as e:
                print(f"Failed to process column {col} of file {file_name}: {e}")

    # Generate the transposed statistical table
    if stats_data:
        generate_stat_table(stats_data, h, k, h_method, k_method)


# main function
def main():
    root = Tk()
    root.title("Input the values of h, k and the calculation method of sigma.")
    Label(root, text="Please enter h value:").grid(row=0)
    h_entry = Entry(root)
    h_entry.grid(row=0, column=1)
    h_entry.insert(0, "7")  # Default h value

    Label(root, text="Please enter k value:").grid(row=1)
    k_entry = Entry(root)
    k_entry.grid(row=1, column=1)
    k_entry.insert(0, "0.5")  # Default k value

    # The calculation method of sigma for H
    h_method_var = StringVar(value='target_percent')
    Label(root, text="Please select sigma for H:").grid(row=2)
    Radiobutton(root, text="Mean", variable=h_method_var, value='mean').grid(row=3, column=0)
    Radiobutton(root, text="Median", variable=h_method_var, value='median').grid(row=3, column=1)
    Radiobutton(root, text="Target/100", variable=h_method_var, value='target_percent').grid(row=3, column=2)

    # The calculation method of sigma for K
    k_method_var = StringVar(value='target_percent')
    Label(root, text="Please select sigma for K:").grid(row=4)
    Radiobutton(root, text="Mean", variable=k_method_var, value='mean').grid(row=5, column=0)
    Radiobutton(root, text="Median", variable=k_method_var, value='median').grid(row=5, column=1)
    Radiobutton(root, text="Target/100", variable=k_method_var, value='target_percent').grid(row=5, column=2)

    def on_submit():
        try:
            h = float(h_entry.get())
            k = float(k_entry.get())
            h_method = h_method_var.get()
            k_method = k_method_var.get()
            if h_method and k_method:
                run_analysis(h, k, h_method, k_method)
                root.destroy()
                print(" Analysis completed！")
            else:
                print(" Please select the sigma calculation method for H and K!")
        except ValueError:
            print(" Both h and k must be entered as numbers!")

    Button(root, text="OK", command=on_submit).grid(row=6, column=1)
    root.mainloop()


if __name__ == "__main__":
    # Automatically create the "data" folder
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f" The data folder has been created. Please place the Excel file into this folder!")
    main()
