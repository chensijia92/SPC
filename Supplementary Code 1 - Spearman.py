import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr
import os
import glob

# --- environment configuration ---
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid")

def aggregate_and_analyze_with_conversion(folder_path):
    # 1. Format conversion steps: Convert .xlsx to .csv
    xlsx_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
    temp_csv_dir = os.path.join(folder_path, "converted_csv")

    if xlsx_files:
        print(f"Found {len(xlsx_files)} Excel files and converting them to CSV...")
        if not os.path.exists(temp_csv_dir):
            os.makedirs(temp_csv_dir)

        for xlsx in xlsx_files:
            try:
                temp_df = pd.read_excel(xlsx, engine='openpyxl')
                base_name = os.path.splitext(os.path.basename(xlsx))[0]
                temp_df.to_csv(os.path.join(temp_csv_dir, f"{base_name}.csv"), index=False, encoding='utf-8-sig')
                print(f"Converted:{os.path.basename(xlsx)}")
            except Exception as e:
                print(f"Conversion of file {xlsx} failed: {e}")

    # 2. Obtain all CSV files
    original_csvs = glob.glob(os.path.join(folder_path, "*.csv"))
    converted_csvs = glob.glob(os.path.join(temp_csv_dir, "*.csv")) if os.path.exists(temp_csv_dir) else []
    all_csv_files = list(set(original_csvs + converted_csvs))

    if not all_csv_files:
        print("No processable .csv or .xlsx files were found.")
        return

    combined_data = {}
    print(f"Processing has begun. A total of {len(all_csv_files)} data sources have been processed...")

    # 3. Traverse the files
    for file_path in all_csv_files:
        try:
            df = pd.read_csv(file_path).dropna(how='all')
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

            if df.empty:
                print(f"The content of the file {os.path.basename(file_path)}  is empty, so it will be skipped.")
                continue

            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna(how='all')

            # Calculate the difference
            df_diff = df.diff().dropna()
            if df_diff.empty:
                continue

            # Match the OARs columns
            prefixes = [col[:-2] for col in df.columns if col.endswith('_V')]
            valid_prefixes = [p for p in prefixes if f"{p}_Dmean" in df.columns]

            for p in valid_prefixes:
                v_col, d_col = f"{p}_V", f"{p}_Dmean"
                if v_col not in df_diff.columns or d_col not in df_diff.columns:
                    continue

                temp_df = df_diff[[v_col, d_col]].copy()
                temp_df.columns = ['Delta_V', 'Delta_Dmean']
                temp_df = temp_df.dropna()

                if len(temp_df) < 1:
                    continue

                if p not in combined_data:
                    combined_data[p] = []
                combined_data[p].append(temp_df)

        except Exception as e:
            print(f"Error occurred while reading the file {os.path.basename(file_path)}: {e}")

    # Exit directly without valid OAR data
    if not combined_data:
        print("No valid organ data was matched (both the XX_V and XX_Dmean columns are required)")
        return

    # 4. output directory
    output_dir = os.path.join(folder_path, "Spearman_plot_results")
    os.makedirs(output_dir, exist_ok=True)
    summary_table = []

    # 5. Drawing and Saving
    print("\nGenerating the summary scatter plot...")
    for organ, dfs_list in combined_data.items():
        try:
            final_df = pd.concat(dfs_list, ignore_index=True)
            final_df = final_df.dropna()

            if len(final_df) < 3:
                print(f"OAR {organ} has insufficient valid points. Skipping.")
                continue

            x = final_df['Delta_V']
            y = final_df['Delta_Dmean']
            rho, p_value = spearmanr(x, y)

            summary_table.append({
                'organ': organ,
                'Total sample points (N)': len(final_df),
                'Spearman_Rho': round(rho, 4),
                'P_Value': p_value,
                'significance': 'significance' if p_value < 0.05 else 'non-significant'
            })

            # plot
            plt.figure(figsize=(9, 7))
            sns.regplot(
                x=x, y=y,
                scatter_kws={'alpha': 0.4, 'color': 'steelblue', 's': 25},
                line_kws={'color': 'darkorange', 'lw': 2}
            )

            stats_info = f"N = {len(final_df)}\nSpearman's ρ = {rho:.3f}\nP = {p_value:.4e}"
            plt.gca().text(0.05, 0.95, stats_info, transform=plt.gca().transAxes,
                           fontsize=16, verticalalignment='top',
                           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

            plt.title(f"{organ} (ΔV vs ΔDmean)", fontsize=16, pad=16)
            plt.xlabel("ΔV (cc)", fontsize=16)
            plt.ylabel("ΔDmean (cGy)", fontsize=16)
            plt.xticks(fontsize=16)
            plt.yticks(fontsize=16)
            plt.tight_layout()

         #   plt.draw()
         #   save_path = os.path.join(output_dir, f"Combined_{organ}.png")
         #   plt.savefig(save_path, dpi=300, facecolor='white', bbox_inches='tight')
         #   plt.close()
         #   print(f" 已保存图片：{save_path}")

            save_path = os.path.join(output_dir, f"Spearman_Combined_{organ}.pdf")
            plt.savefig(save_path, format='pdf', facecolor='white', bbox_inches='tight')
            plt.close()
            print(f" Saved PDF：{save_path}")

        except Exception as e:
            print(f" OAR {organ} Drawing failed: {str(e)}")

    # 6. Save the summary table
    if summary_table:
        res_df = pd.DataFrame(summary_table)
        csv_path = os.path.join(output_dir, "Correlation analysis results.csv")
        res_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n📊 The summary table has been saved：{csv_path}")

    print(f"\n🎉 All tasks completed！")

# --- Start ---
if __name__ == "__main__":
    target_folder = r'D:\Work\choice\MP\pythonProject1\data home'
    aggregate_and_analyze_with_conversion(target_folder)
