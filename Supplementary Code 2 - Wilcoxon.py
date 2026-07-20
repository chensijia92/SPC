import pandas as pd
import numpy as np
import os
import glob
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import wilcoxon
import gc

# basic setting
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid", font='SimHei')
plt.rcParams['font.family'] = 'Arial'


# Set the font size for all text uniformly
plt.rcParams['font.size'] = 20
plt.rcParams['axes.titlesize'] = 24
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 16
plt.rcParams['ytick.labelsize'] = 16

def run_fraction_analysis_final_version(folder_path):
    file_list = glob.glob(os.path.join(folder_path, "*.csv"))
    if not file_list: return

    target_indices = [0, 14, 32] 
    labels = ["1", "15", "33"]
    data_pool = {}

    # 1. Extract Data
    for file_path in file_list:
        try:
            df = pd.read_csv(file_path, nrows=34).dropna(how='all', axis=0)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            for col in df.columns:
                if col not in data_pool: data_pool[col] = {idx: [] for idx in target_indices}
                for idx in target_indices:
                    if idx < len(df):
                        val = df.iloc[idx][col]
                        if pd.notnull(val): data_pool[col][idx].append(val)
        except:
            pass

    output_dir = os.path.join(folder_path, "Wilcoxon_boxplot_results")
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    # 2. Parameter-by-parameter analysis
    for param, f_data in data_pool.items():
        plot_df = []
        for i, idx in enumerate(target_indices):
            for val in f_data[idx]:
                plot_df.append({"Fraction": labels[i], "Value": val})
        pdf = pd.DataFrame(plot_df)
        if pdf.empty or pdf['Fraction'].nunique() < 3: continue

        # statistical calculation (Wilcoxon)
        p_vals = {}
        pairs = [(0, 14, "1v15"), (14, 32, "15v33"), (0, 32, "1v33")]
        for idx1, idx2, key in pairs:
            g1, g2 = np.array(f_data[idx1]), np.array(f_data[idx2])
            if len(g1) == len(g2) and len(g1) >= 5:
                if np.all(g1 == g2):
                    p_vals[key] = 1.0
                else:
                    _, p = wilcoxon(g1, g2, zero_method="pratt")
                    p_vals[key] = p
            else:
                p_vals[key] = None

        # 3. Plot
        fig, ax = plt.subplots(figsize=(8, 8))

        # Color box plot
        sns.boxplot(x="Fraction", y="Value", data=pdf, hue="Fraction", palette="Set3", legend=False, ax=ax)

        # Scatter plot: Set jitter=False to arrange the points centrally and prevent them from scattering.
        sns.stripplot(x="Fraction", y="Value", data=pdf, color=".25", alpha=0.5, jitter=False, ax=ax)

        # Reserved space for coordinate axes
        y_min, y_max = pdf['Value'].min(), pdf['Value'].max()
        y_range = y_max - y_min if y_max != y_min else 1.0
        ax.set_ylim(y_min - y_range * 0.1, y_max + y_range * 0.7)

        # Mark specific values (black)
        def add_p_value_annotation(ax, x1, x2, p, v_offset):
            if p is None: return
            p_text = f"p = {p:.4f}" if p >= 0.001 else f"p = {p:.2e}"
            weight = "bold" if p < 0.05 else "normal"
            y_line = y_max + v_offset
            h_bracket = y_range * 0.03
            ax.plot([x1, x1, x2, x2], [y_line - h_bracket, y_line, y_line, y_line - h_bracket], color="black", lw=1.2)
            ax.text((x1 + x2) / 2, y_line + h_bracket * 0.2, p_text, ha='center', va='bottom', color="black",
                    fontsize=16, fontweight=weight)

        # Draw the three-layer P-values
        add_p_value_annotation(ax, 0, 1, p_vals.get("1v15"), y_range * 0.1)
        add_p_value_annotation(ax, 1, 2, p_vals.get("15v33"), y_range * 0.28)
        add_p_value_annotation(ax, 0, 2, p_vals.get("1v33"), y_range * 0.46)

        ax.set_title(f"{param}", pad=20, fontsize=14)

        # Set the title for the Y-axis
        ax.set_ylabel("Dose(cGy)", fontsize=16)

        # Set the title for the X-axis
        ax.set_xlabel("Fraction", fontsize=16)

        plt.tight_layout()

        #save_path = os.path.join(output_dir, f"{param}_Final_Centered.png")
       # plt.savefig(save_path, dpi=200, bbox_inches='tight')
       # plt.close(fig)
       # gc.collect()

        save_path = os.path.join(output_dir, f"{param}_wilcoxon.pdf")
        plt.savefig(save_path, format='pdf', bbox_inches='tight')
        plt.close(fig)
        gc.collect()

    print(f"Processing completed! The chart has been saved:{output_dir}")


if __name__ == "__main__":
    # Perform the analytics
    run_fraction_analysis_final_version(r'D:\Work\choice\MP\pythonProject1\data home')