import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_excel('GL for Expenses.xlsx')  # Replace 'your_file.xlsx' with the actual file path
cost_column = df['Amt in local cur.']
def benford_probability(digit):
    return np.log10(1 + 1/digit)
first_digits = cost_column.astype(str).str.replace('.', '').str.replace('-', '').str[0].astype(int)
digit_counts = first_digits.value_counts().sort_index()
total_count = digit_counts.sum()
digits = np.arange(1, 10)
probabilities = [benford_probability(d) * total_count for d in digits]
plt.bar(digits, probabilities, color='skyblue', label="Benford's Law", alpha=0.7)  # Adjust transparency here
plt.bar(digit_counts.index, digit_counts.values, color='orange', label='Actual Data', alpha=0.7)  # Adjust transparency here
plt.xlabel('Digit')
plt.ylabel('Frequency')
plt.title("Benford's Law vs Actual Data (Cost Column)")
plt.legend()
plt.show()
total_count = digit_counts.sum()
actual_percentages = (digit_counts / total_count) * 100
benford_percentages = [np.log10(1 + 1/digit) * 100 for digit in range(1, 10)]
plt.plot(digits, actual_percentages, marker='o', linestyle='-', color='orange', label='Actual Data')
plt.plot(digits, benford_percentages, marker='o', linestyle='-', color='skyblue', label="Benford's Law")
plt.xlabel('Digit')
plt.ylabel('Frequency (%)')
plt.title("Percentage of First Digit Frequency (Cost Column)")
plt.legend()
plt.show()