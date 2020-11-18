#!/usr/bin/env python3

import numpy as np
import scipy
import scipy.stats
import matplotlib.pyplot as plt


def linear_fit(x,y,printinfo=True):
    """
    Returns slope, intercept, slope error, intercept error, y error
    All from https://en.wikipedia.org/wiki/Simple_linear_regression
    on 2019-08-26
    Useage:
        if you have 1D arrays of x and y values in variables x and y:
        call like:
        slope, intercept, slopeerror, intercepterror, yerr = linear_fit(x,y)
        
    """

    if len(x) != len(y):
        raise Exception("Length of x and y data must be the same!")

    x = scipy.array(x)
    y = scipy.array(y)
    N = len(x)
    meanx = scipy.mean(x)
    meany = scipy.mean(y)
    variancex = sum((x-meanx)**2)
    variancey = sum((y-meany)**2)
    covariance = sum((x-meanx)*(y-meany))

    slope = covariance / variancex
    intercept = meany - meanx*slope
    r2 = covariance**2 / variancex / variancey

    residuals = y - (slope*x+intercept)
    yvariance = sum(residuals**2/(N-2))

    slopevariance = yvariance/variancex
    interceptvariance = slopevariance * sum(x**2 / N)
    
    slopeerror = scipy.sqrt(slopevariance)
    intercepterror = scipy.sqrt(interceptvariance)
    yerr = scipy.sqrt(yvariance)

    if printinfo:
      onesigtailProb = scipy.stats.norm.sf(1)
      up1sigChiVal = scipy.stats.chi.ppf(onesigtailProb,df=N-2)
      down1sigChiVal = scipy.stats.chi.isf(onesigtailProb,df=N-2)
      yerrupBound =  yerr*(scipy.sqrt(N-2)/up1sigChiVal - 1)
      yerrdownBound =  yerr*(1 - scipy.sqrt(N-2)/down1sigChiVal)
      #yerrupBound =  scipy.sqrt(N-2)*yerr/up1sigChiVal
      #yerrdownBound =  scipy.sqrt(N-2)*yerr/down1sigChiVal
      #print(onesigtailProb)
      #print(up1sigChiVal)
      #print(down1sigChiVal)
      print("#"*80)
      print("Linear Fit Results for {} Data Points".format(N))
      print("slope estimate:               {:10.5g} +/- {:10.5g}".format(slope,slopeerror))
      print("intercept estimate:           {:10.5g} +/- {:10.5g}".format(intercept,intercepterror))
      print("y point uncertainty estimate: {:10.5g}   +{:<10.5g} -{:<10.5g}".format(yerr,yerrupBound,yerrdownBound))
      print("r^2:                          {:10.5g}".format(r2))
      print("#"*80)

    return slope, intercept, slopeerror, intercepterror, yerr

def plot_linear_fit(ax, xdata, slope,intercept,slopeerror, intercepterror, yerr):
    ax.plot(xdata,slope*xdata+intercept,label=f"Fit: y = {slope:.3g}x+{intercept:.3g}")

N = 1000

lambdas = np.linspace(0.5,20,10)
means = np.zeros(lambdas.shape)
stds = np.zeros(lambdas.shape)
variances = np.zeros(lambdas.shape)

for i in range(len(lambdas)):
    data = np.random.poisson(lambdas[i],N)
    means[i] = np.mean(data*4.5)
    stds[i] = 20+np.std(data*4.5)
    variances[i] = 400+np.var(data*4.5)

stds_results = linear_fit(means,stds)
variances_results = linear_fit(means,variances)
fig, ax = plt.subplots()
ax.scatter(means,stds)
plot_linear_fit(ax,means,*stds_results)
ax.legend()
fig.savefig("toy_stdsVmeans.png")
fig, ax = plt.subplots()
ax.scatter(means,variances)
plot_linear_fit(ax,means,*variances_results)
ax.legend()
fig.savefig("toy_variancesVmeans.png")
print(f"1/slope: {1/variances_results[0]}")
