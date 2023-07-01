import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
import matplotlib.pyplot as plt


# Make a scatter plot from a sinlge set of XY data
# For determining if the Y values have a measurable effect on the X values
# and if further X values could be predicted
def scat_plot(x, y, name):
    sns.set_theme()
    sns.set_style("whitegrid")
    fig, ax = plt.subplots()
    ax.set_title(name)
    x_name = "Irradiation dose [kGy]"
    y_name = f"Density [g/cm\N{SUPERSCRIPT THREE}]"
    ax.set_xlabel(x_name)
    ax.set_ylabel(y_name)
    # Only show the x-axis ticks that actually represent measurements
    ax.set_xticks(np.array(x))
    color1 = "palevioletred"
    color2 = "royalblue"

    # Not really using these values anywhere atm
    slope, intercept, r, p, std_err = stats.linregress(x, y)
    r_text = f"Correlation coefficient: {round(r, 4)}"
    p_text = f"P-value for a hypothesis that the slope is zero: {round(p, 4)}"
    std_err_text = f"Standard error of the estimated slope: {str(std_err)[:5]} e{str(std_err)[-3:]}"
    ax.legend(title=f"{r_text}\n{p_text}\n{std_err_text}", loc="upper center")

    # Get the confidence bands around the linear regression line
    df = pd.DataFrame(list(zip(x, y)), columns=["dose", "density"])
    x_to_pred = sm.add_constant(df["dose"].values)
    ols_model = sm.OLS(df["density"].values, x_to_pred)
    est = ols_model.fit()
    y_pred = est.predict(x_to_pred)
    x_pred = df.dose.values
    pred = est.get_prediction(x_to_pred).summary_frame()

    # Color the actuall data ticks accoring to wheter they are inside or outside the confidence bands
    for i in range(0, len(x)):
        if pred["mean_ci_lower"][i] < y[i] < pred["mean_ci_upper"][i]:
            col = color2
        else:
            col = color1
        ax.scatter(x[i], y[i], c=col)

    # Plot the linear regression line, confidence bands are shows as an area
    ax.plot(x_pred, y_pred, color="black")
    ax.fill_between(
        x_pred, pred["mean_ci_lower"], pred["mean_ci_upper"], color="black", alpha=0.1
    )

    plt.gcf().set_size_inches(16, 9)
    plt.savefig(f"{name}.png")
    plt.close()


if __name__ == "__main__":
    dose = [0, 15, 33, 45, 66, 99, 132, 165, 195]
    density_pa6 = [9.213, 9.220, 9.231, 9.210, 9.203, 9.182, 9.200, 9.164, 9.206]
    density_pa66 = [9.224, 9.277, 9.256, 9.248, 9.226, 9.227, 9.221, 9.237, 9.233]

    scat_plot(dose, density_pa6, "PA 6")
    scat_plot(dose, density_pa66, "PA 6.6")
