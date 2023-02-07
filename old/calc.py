from logging import getLogger
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from uncertainties import ufloat

mylogger = getLogger("driver")
name = "calc"


def ptp(x):
    return np.abs(np.nanmax(x) - np.nanmin(x))


def ptpe(x, ptp):
    return np.mean([np.abs(np.nanmin(-x + ptp / 2)), np.abs(np.nanmax(x - ptp / 2))])


def rms(x):
    return np.sqrt(np.nanmean(x ** 2))


def rmse(x, rms):
    return np.nan


def lin_fit(V, R, I_0):
    return V / R + I_0


def cos_fit(t, A, t_0, phi, A_0):
    return A * np.sin(2 * np.pi * t / t_0 + phi) + A_0


def cos_fit_phi(A, t_0, A_0):
    def temp_cos_fit(t, phi, A=A, t_0=t_0, A_0=A_0):
        return cos_fit(t, A, t_0, phi, A_0)

    return temp_cos_fit


def cos_fit_A(t_0, phi, A_0):
    def temp_cos_fit(t, A, phi=phi, t_0=t_0, A_0=A_0):
        return cos_fit(t, A, t_0, phi, A_0)

    return temp_cos_fit


def resistances(data, offs, config, setup):
    """
    Return data in SI units
    :param data:
    :param offs:
    :param config:
    :param setup:
    :return:
    """
    # Calculating I, V, t
    offsets = (np.mean(offs["V_sample_1"]), np.mean(offs["V_sample_2"]))
    V = np.array((data["V_sample_1"] - offsets[0]) / setup["femto_A"], dtype="float64")  # V
    I = np.array(
        (data["V_sample_2"] - offsets[1]) / setup["R_ref"] / setup["femto_B"], dtype="float64"
    )  # A
    t = (
        np.linspace(0, 1, num=len(V))
        * config["chunks"]
        / np.mean(config["source_frequency"], dtype="float64")
    )  # s

    # Calculating Peak-to-Peak Amplitudes and Resistance
    V_ptp, I_ptp = ptp(V), ptp(I)
    V_ptp_err, I_ptp_err = ptpe(V, V_ptp), ptpe(I, I_ptp)
    R_ptp = V_ptp / I_ptp  # Ohm
    R_ptp_err = np.abs(1 / I_ptp) * V_ptp_err + np.abs(-V_ptp * I_ptp ** (-2)) * I_ptp_err

    # Calculating Root-Mean-Square Amplitudes and Resistance
    V_rms, I_rms = rms(V), rms(I)
    V_rms_err, I_rms_err = rmse(V, V_rms), rmse(I, I_rms)
    R_rms = V_rms / I_rms  # Ohm
    R_rms_err = np.abs(1 / I_rms) * V_rms_err + np.abs(-V_rms * I_rms ** (-2)) * I_rms_err

    # Obtaining Resistance by linear I,V fit
    R_popt, R_pcov = curve_fit(lin_fit, V, I, p0=[V_rms / I_rms, 0])
    R_perr = np.sqrt(np.diag(R_pcov))
    R_lin, I_0 = R_popt  # Ohm, A
    R_lin_err, I_0_err = R_perr  # Ohm, A

    # Obtaining Amplitudes and Impedance by cosinusoidal fit
    ## Pre-Fitting
    t_0 = 1 / config["source_frequency"][0]  # s

    # Fitting Phase
    V_phi, V_phi_pcov = curve_fit(
        cos_fit_phi(A=V_rms / np.sqrt(2), t_0=t_0, A_0=I_0 * R_lin),
        t,
        V,
        p0=0,
        bounds=(0, 2 * np.pi),
        method="dogbox",
    )
    I_phi, I_phi_pcov = curve_fit(
        cos_fit_phi(A=I_rms / np.sqrt(2), t_0=t_0, A_0=I_0),
        t,
        I,
        p0=0,
        bounds=(0, 2 * np.pi),
        method="dogbox",
    )

    # Fitting Amplitude
    V_max, V_max_pcov = curve_fit(
        cos_fit_A(t_0=t_0, phi=V_phi, A_0=I_0 * R_lin),
        t,
        V,
        p0=0,
        bounds=(-V_ptp * 1.5, V_ptp * 1.5),
        method="dogbox",
    )
    I_max, I_max_pcov = curve_fit(
        cos_fit_A(t_0=t_0, phi=I_phi, A_0=I_0),
        t,
        I,
        p0=I_ptp,
        bounds=(-I_ptp * 1.5, I_ptp * 1.5),
        method="dogbox",
    )

    # Pre-Calculating Amplitude / Phase
    V_max, I_max = V_max[0], I_max[0]  # V, A
    V_phi, I_phi = V_phi[0], I_phi[0]  # rad

    ## Real-Fitting
    V_popt, V_pcov = curve_fit(cos_fit, t, V, p0=[V_max, t_0, V_phi, I_0 * R_lin])
    V_max, V_t0, V_phi, V_A0 = V_popt
    V_max_err, V_t0_err, V_phi_err, V_A0_err = np.sqrt(np.diag(V_pcov))
    I_popt, I_pcov = curve_fit(cos_fit, t, I, p0=[I_max, t_0, I_phi, I_0])
    I_max, I_t0, I_phi, I_A0 = I_popt
    I_max_err, I_t0_err, I_phi_err, I_A0_err = np.sqrt(np.diag(I_pcov))

    # Calculating Impedance
    R_cos = V_max / I_max  # Ohm
    R_cos_err = np.abs(1 / I_max) * V_max_err + np.abs(-V_max * I_max ** (-2)) * I_max_err
    phi = (V_phi - I_phi)%(2*np.pi)  # rad
    phi_err = np.abs(V_phi_err) + np.abs(I_phi_err)

    # Return the derived Values in SI units
    resi = {
        "V": V,
        "I": I,
        "t": t,
        "__ptp__": "_______",
        "R_ptp": ufloat(R_ptp, R_ptp_err),
        "V_ptp": ufloat(V_ptp, V_ptp_err),
        "I_ptp": ufloat(I_ptp, I_ptp_err),
        "__rms__": "_______",
        "R_rms": ufloat(R_rms, R_rms_err),
        "V_rms": ufloat(V_rms, V_rms_err),
        "I_rms": ufloat(I_rms, I_rms_err),
        "__lin__": "_______",
        "R_lin": ufloat(R_lin, R_lin_err),
        "I_0": ufloat(I_0, I_0_err),
        "__cos__": "_______",
        "R_cos": ufloat(R_cos, R_cos_err),
        "phi": ufloat(phi, phi_err),
        "V_max": ufloat(V_max, V_max_err),
        "V_t0": ufloat(V_t0, V_t0_err),
        "V_phi": ufloat(V_phi, V_phi_err),
        "V_A0": ufloat(V_A0, V_A0_err),
        "I_max": ufloat(I_max, I_max_err),
        "I_t0": ufloat(I_t0, I_t0_err),
        "I_phi": ufloat(I_phi, I_phi_err),
        "I_A0": ufloat(I_A0, I_A0_err),
    }

    # Logging
    mylogger.info(f"({name}) R_ptp: {resi['R_ptp']:.3e} Ohm")
    mylogger.info(f"({name}) R_rms: {resi['R_rms']:.3e} Ohm")
    mylogger.info(f"({name}) R_lin: {resi['R_lin']:.3e} Ohm")
    mylogger.info(f"({name}) R_cos: {resi['R_cos']:.3e} Ohm")
    mylogger.info(f"({name}) phi: {resi['phi']:.2e} rad")
    mylogger.info(f"({name}) V_ptp: {resi['V_ptp']:.2e} V")
    mylogger.info(f"({name}) I_ptp: {resi['I_ptp']:.2e} A")
    mylogger.info(f"({name}) V_rms: {resi['V_rms']:.2e} V")
    mylogger.info(f"({name}) I_rms: {resi['I_rms']:.2e} A")
    mylogger.info(f"({name}) I_0: {resi['I_0']:.2e} A")
    mylogger.info(f"({name}) V_max: {resi['V_max']:.2e} V")
    mylogger.info(f"({name}) t_0: {resi['V_t0']:.2e} s")
    mylogger.info(f"({name}) V_phi: {resi['V_phi']:.2e} rad")
    mylogger.info(f"({name}) V_0: {resi['V_A0']:.2e} A")
    mylogger.info(f"({name}) I_max: {resi['I_max']:.2e} A")
    mylogger.info(f"({name}) t_0: {resi['I_t0']:.2e} s")
    mylogger.info(f"({name}) I_phi: {resi['I_phi']:.2e} rad")
    mylogger.info(f"({name}) I_0: {resi['I_A0']:.2e} A")

    return resi



def plotting(data, offs, setup, resi={}, config={}, figsize = (12, 6.75), list=[1,2,3]):
    if 1 in list:
        raw_signal_plotting(data, offs, setup, config, resi, figsize=figsize)
    if 2 in list:
        sweep_plotting(resi, figsize = figsize)
    if 3 in list:
        IV_plotting(offs, setup, resi, figsize = figsize)
    plt.show()

def raw_signal_plotting(data, offs, setup, config, resi, figsize=(12, 6.75)):

    if resi == {}:
        offsets = (np.mean(offs["V_sample_1"]), np.mean(offs["V_sample_2"]))
        V = np.array((data["V_sample_1"] - offsets[0]) / setup["femto_A"], dtype="float64")  # V
        I = np.array(
            (data["V_sample_2"] - offsets[1]) / setup["R_ref"] / setup["femto_B"], dtype="float64"
        )  # A
        resi["t"] = (
            np.linspace(0, 1, num=len(V))
            * config["chunks"]
            / np.mean(config["source_frequency"], dtype="float64")
        )  # s
        if config=={}:
            print("please give either resi or config")

    # Signal
    fig, (ax1, ax2a, ax2b) = plt.subplots(3, sharex="all", num=1, figsize=figsize)

    # Power Source
    ax1.title.set_text(r"Power Source Output")
    ax1.plot(resi["t"], data["V_source_1"], "b.", label=r"$V^+$")
    ax1.plot(resi["t"], data["V_source_2"], "r.", label=r"$V^-$")
    ax1.set_ylabel("Voltage [V]")
    ax1.legend(loc="upper right")
    ax1.grid()

    # Multimeter
    ax2a.title.set_text(r"Multimeter Raw Signal - Voltage")
    ax2a.plot(resi["t"], data["V_sample_1"], "r.")
    ylim_2a = ax2a.get_ylim()
    ax2a.axhline(
        y=np.mean(offs["V_sample_1"]),
        color="r",
        linestyle="--",
        label=f"offset ({np.mean(offs['V_sample_1']):.1e} V)",
    )
    ax2a.fill_between(
        resi["t"],
        -setup["multi1_range"],
        setup["multi1_range"],
        color="r",
        alpha=0.15,
        label=f"range ({setup['multi1_range']:.1e} V)",
    )
    ax2a.set_ylim(ylim_2a)
    ax2a.set_ylabel("Voltage [V]", color="r")
    ax2a.tick_params(axis="y", labelcolor="r")
    ax2a.grid()
    ax2a.legend(loc="upper right")

    # ax2b = ax2a.twinx()
    ax2b.title.set_text(r"Multimeter Raw Signal - Current")
    ax2b.plot(resi["t"], data["V_sample_2"], "b.")
    ylim_2b = ax2b.get_ylim()
    ax2b.axhline(
        y=np.mean(offs["V_sample_2"]),
        color="b",
        linestyle="--",
        label=f"offset ({np.mean(offs['V_sample_2']):.1e} V)",
    )
    ax2b.fill_between(
        resi["t"],
        -setup["multi2_range"],
        setup["multi2_range"],
        color="b",
        alpha=0.15,
        label=f"range ({setup['multi2_range']:.1e} V)",
    )
    ax2b.set_ylim(ylim_2b)
    ax2b.set_ylabel("Voltage [V]", color="b")
    ax2b.tick_params(axis="y", labelcolor="b")
    ax2b.grid()
    ax2b.legend(loc="upper right")
    plt.tight_layout()



def sweep_plotting(resi, figsize = (12, 6.75)):

    fig, (ax3a, ax3b) = plt.subplots(2, num=2, figsize=figsize)
    ax3a.title.set_text(
        r"Signal at Sample, Fit: $A(t)=A_{max}\cdot\cos(2\pi\cdot t/t_0 + \varphi) + A_0$"
    )
    ax3a.set_xlabel("time [s]")
    ax3a.set_ylabel("Voltage [V]", color="red")
    ax3a.tick_params(axis="y", labelcolor="red")
    ax3a.plot(resi["t"], resi["V"], "r.")
    xlim = ax3a.get_xlim()
    ax3a.axhline(
        y=resi["V_ptp"].nominal_value / 2,
        linestyle="--",
        color="r",
        label=fr"$V_{{ptp}} = ${resi['V_ptp']/2:.2e}$\,$V",
    )
    ax3a.axhline(y=-resi["V_ptp"].nominal_value / 2, linestyle="--", color="r")
    ax3a.fill_between(
        xlim,
        resi["V_ptp"].nominal_value / 2 + resi["V_ptp"].std_dev,
        resi["V_ptp"].nominal_value / 2 - resi["V_ptp"].std_dev,
        color="red",
        alpha=0.15,
    )
    ax3a.fill_between(
        xlim,
        -resi["V_ptp"].nominal_value / 2 + resi["V_ptp"].std_dev,
        -resi["V_ptp"].nominal_value / 2 - resi["V_ptp"].std_dev,
        color="red",
        alpha=0.15,
    )
    ax3a.axhline(
        y=resi["V_rms"].nominal_value,
        linestyle="-.",
        color="r",
        label=fr"$V_{{rms}} = ${resi['V_rms']:.2e}$\,$V",
    )
    ax3a.axhline(y=-resi["V_rms"].nominal_value, linestyle="-.", color="r")
    lab0 = r"$V_{{max}} = $%s$\,$V" % str(f"{resi['V_max']:.2e}")
    lab1 = fr"$t_{{0}} = ${resi['V_t0']:.2e}$\,$s"
    lab2 = fr"$\varphi = ${resi['V_phi']:.2e}$\,$rad"
    lab3 = fr"$V_{{0}} = ${resi['V_A0']:.2e}$\,$V"
    ax3a_label = f"{lab0}\n{lab1}\n{lab2}\n{lab3}"
    ax3a.plot(
        resi["t"],
        cos_fit(
            resi["t"],
            *[
                resi["V_max"].nominal_value,
                resi["V_t0"].nominal_value,
                resi["V_phi"].nominal_value,
                resi["V_A0"].nominal_value,
            ],
        ),
        "r-",
        label=ax3a_label,
    )
    ax3a.grid()
    ax3a.legend(loc="upper right")

    # ax3b = ax3a.twinx()
    ax3b.set_ylabel("Current [A]", color="blue")
    ax3b.tick_params(axis="y", labelcolor="blue")
    ax3b.plot(resi["t"], resi["I"], "b.")
    ax3b.axhline(
        y=resi["I_ptp"].nominal_value / 2,
        linestyle="--",
        color="b",
        label=fr"$I_{{ptp}} = ${resi['I_ptp']/2:.2e}$\,$V",
    )
    ax3b.axhline(y=-resi["I_ptp"].nominal_value / 2, linestyle="--", color="b")
    ax3b.fill_between(
        xlim,
        resi["I_ptp"].nominal_value / 2 + resi["I_ptp"].std_dev,
        resi["I_ptp"].nominal_value / 2 - resi["I_ptp"].std_dev,
        color="blue",
        alpha=0.15,
    )
    ax3b.fill_between(
        xlim,
        -resi["I_ptp"].nominal_value / 2 + resi["I_ptp"].std_dev,
        -resi["I_ptp"].nominal_value / 2 - resi["I_ptp"].std_dev,
        color="blue",
        alpha=0.15,
    )
    ax3b.axhline(
        y=resi["I_rms"].nominal_value,
        linestyle="-.",
        color="b",
        label=fr"$I_{{rms}} = ${resi['I_rms']:.2e}$\,$V",
    )
    ax3b.axhline(y=-resi["I_rms"].nominal_value, linestyle="-.", color="b")
    lab0 = fr"$I_{{max}} = ${resi['I_max']:.2e}$\,$V"
    lab1 = fr"$t_{{0}} = ${resi['I_t0']:.2e}$\,$s"
    lab2 = fr"$\varphi = ${resi['I_phi']:.2e}$\,$rad"
    lab3 = fr"$I_{{0}} = ${resi['I_A0']:.2e}$\,$V"
    ax3b_label = f"{lab0}\n{lab1}\n{lab2}\n{lab3}"
    ax3b.plot(
        resi["t"],
        cos_fit(
            resi["t"],
            *[
                resi["I_max"].nominal_value,
                resi["I_t0"].nominal_value,
                resi["I_phi"].nominal_value,
                resi["I_A0"].nominal_value,
            ],
        ),
        "b-",
        label=ax3b_label,
    )
    ax3b.grid()
    ax3b.legend(loc="upper right")
    ax3b.set_xlabel("time [s]")
    plt.tight_layout()


def IV_plotting(offs, setup, resi, figsize=(12, 6.75)):
    # I-V Characteristics
    fig, ax4 = plt.subplots(1, num=3, figsize=figsize)
    ax4.title.set_text(r"I-V Characteristics, Fit: $I(V)=V/R_{lin}\cdot I_0$")
    ax4.plot(resi["V"], resi["I"], "b.", label="data points")
    ax4.plot(
        resi["V"],
        lin_fit(resi["V"], *[resi["R_lin"].nominal_value, resi["I_0"].nominal_value]),
        "r-",
        label="linear fit:\n"
        fr"$R_{{lin}} = ${resi['R_lin']:.2e}$\,\Omega$"
        "\n"
        fr"$I_0 = ${resi['I_0']:.2e}$\,$A",
    )
    xlim = ax4.get_xlim()
    ylim = ax4.get_ylim()

    xrange = (setup["multi1_range"] - np.mean(offs["V_sample_1"])) / setup["femto_A"]
    yrange = (
        (setup["multi2_range"] - np.mean(offs["V_sample_2"])) / setup["femto_B"] / setup["R_ref"]
    )
    ax4.fill_between(
        [-xrange, xrange],
        -yrange,
        yrange,
        color="grey",
        alpha=0.15,
        label="within range:\n" fr"$\pm${xrange:.1e}$\,$V, " fr"$\pm${yrange:.1e}$\,$A",
    )
    ax4.set_xlabel("Voltage [V]")
    ax4.set_ylabel("Current [A]")
    ax4.set_xlim(xlim)
    ax4.set_ylim(ylim)
    ax4.grid()
    ax4.legend()
    plt.tight_layout()




"""

    # R-V Characteristics
    fig, ax5 = plt.subplots(1, num=4, figsize=figsize)
    ax5.title.set_text(r"R-V Characteristics")
    ax5.plot(resi["V"], resi["V"] / resi["I"], "b.", label="data points")
    ax5.axhline(
        y=resi["R_lin"].nominal_value,
        color="red",
        linestyle="-",
        label=fr"$R_{{lin}} = ${resi['R_lin']:.2e}$\,\Omega$",
    )
    ax5.set_xlabel("Voltage [V]")
    ax5.set_ylabel(r"Resistance [$\Omega$]")
    ax5.grid()
    ax5.legend()
    plt.tight_layout()
    
    # R-V Characteristics
    fig, ax6 = plt.subplots(1, num=5, figsize=figsize)
    ax6.title.set_text(r"V-V Source Characteristic")
    ax6.plot(data["V_source_1"], data["V_source_2"], "b.", label="data points")
    ax6.plot(data["V_source_1"], -data["V_source_1"], "r-", label="lin")
    ax6.set_xlabel("Voltage [V]")
    ax6.set_ylabel("Voltage [V]")
    ax6.grid()
    ax6.legend()
    plt.tight_layout()

"""
