import matplotlib.pyplot as plt
import csv
import os

actual_unique = 32091
estimated_unique = 49032
accuracy = 47.2

if os.path.exists("results.csv"):
    with open("results.csv", "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row[0] == "actual_unique":
                actual_unique = float(row[1])
            elif row[0] == "estimated_unique":
                estimated_unique = float(row[1])
            elif row[0] == "accuracy":
                accuracy = float(row[1])

labels = ['Actual Unique Users', 'Estimated (Flajolet-Martin)']
values = [actual_unique, estimated_unique]
colors = ['#2c3e50', '#3498db']

plt.figure(figsize=(8, 6))
bars = plt.bar(labels, values, color=colors, width=0.5)

for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 1000, f"{int(yval)}", ha='center', va='bottom', fontsize=12)

plt.title('Cardinality Estimation: Flajolet-Martin vs Actual', fontsize=14, fontweight='bold')
plt.suptitle(f'Estimation Accuracy: {accuracy:.2f}%', fontsize=11, color='gray', y=0.92)
plt.ylabel('Number of Unique Users', fontsize=12)
plt.ylim(0, max(values) * 1.2)

plt.tight_layout()
plt.savefig('fm_accuracy_plot.png', dpi=300)
print("Plot successfully saved to fm_accuracy_plot.png!")
