import pandas as pd

parametros = "parametros.xlsx"

costos_df = pd.read_excel(parametros, sheet_name="costos")
capb_df = pd.read_excel(parametros, sheet_name="capb_ik")
capc_df = pd.read_excel(parametros, sheet_name="capc_ic")
cmb_df = pd.read_excel(parametros, sheet_name="cmb_ik")
cmc_df = pd.read_excel(parametros, sheet_name="cmc_ic")
cd_df = pd.read_excel(parametros, sheet_name="cd_ikc")
s0_df = pd.read_excel(parametros, sheet_name="s0_ika")
i0_df = pd.read_excel(parametros, sheet_name="i0_ica")
b_df = pd.read_excel(parametros, sheet_name="b_t")
demanda_df = pd.read_excel(parametros, sheet_name="d_ictw")
alpha_df = pd.read_excel(parametros, sheet_name="alpha_i")
li_df = pd.read_excel(parametros, sheet_name="L_i")
h_df = pd.read_excel(parametros, sheet_name="h_ct")

#CONJUNTOS
I = sorted(costos_df["medicamento"].unique())
C = sorted(capc_df["CESFAM"].unique())
K = sorted(capb_df["bodega"].unique())
T = range(1, 53)
Omega = ["Baja", "Normal", "Alta"]

#df de parámetros
CC_i = dict(zip(costos_df["medicamento"], costos_df["CC_i"]))
CE_i = dict(zip(costos_df["medicamento"], costos_df["CE_i"]))
CQ_i = dict(zip(costos_df["medicamento"], costos_df["CQ_i"]))
CVc_i = dict(zip(costos_df["medicamento"], costos_df["CVc_i"]))
CVb_i = dict(zip(costos_df["medicamento"], costos_df["CVb_i"]))

#Parámetros
F_k = 15000000
Gamma = 56534100
M = 10**4

# --- FIX BUG 2: G_kt estaba en CAJAS (79.026), mientras CapB y H_ct del Excel
# ya están en UNIDADES (comprimidos). El factor comprimidos/caja con que se
# construyó H_ct es 250 (p.ej. 4.017 cajas -> 1.004.250 unidades). Se aplica el
# mismo factor para dejar G_kt en unidades y que sea consistente con el resto.
UNIDADES_POR_CAJA = 250
G_kt = 79026 * UNIDADES_POR_CAJA   # = 19.756.500 unidades/semana

alpha_i = dict(zip(alpha_df["medicamento"], alpha_df["nivel"]))

L_i = dict(zip(li_df["medicamento"], li_df["vida_util"]))

#el conjunto A depende de Li
A = {i: range(1, int(L_i[i]) + 1) for i in I}

factor = {
    "Baja": 0.8,
    "Normal": 1,
    "Alta": 1.25
}

Capb_ik = {
    (row["medicamento"], row["bodega"]): row["capacidad"]
    for _, row in capb_df.iterrows()
}

Capc_ic = {
    (row["medicamento"], row["CESFAM"]): row["capacidad"]
    for _, row in capc_df.iterrows()
}

CMb_ik = {
    (row["medicamento"], row["bodega"]): row["costo"]
    for _, row in cmb_df.iterrows()
}

CMc_ic = {
    (row["medicamento"], row["CESFAM"]): row["costo"]
    for _, row in cmc_df.iterrows()
}

CD_ikc = {
    (row["medicamento"], row["bodega"], row["CESFAM"]): row["costo"]
    for _, row in cd_df.iterrows()
}

# --- FIX BUG 1: el inventario inicial se ubica SIEMPRE en la edad a = L_i del
# medicamento (vida útil remanente completa, según el supuesto del informe).
# Antes la clave usaba la columna "edad" del Excel; si esa edad no coincidía
# con L_i, el lookup S0_ika.get((i,k,L_i[i]),0) del modelo devolvía 0 y se
# perdía el stock de 4 de los 5 medicamentos. Forzar la edad a L_i hace el
# código robusto aunque la columna "edad" del Excel venga mal.
S0_ika = {
    (row["medicamento"], row["bodega"], int(L_i[row["medicamento"]])): row["inventario"]
    for _, row in s0_df.iterrows()
}

I0_ica = {
    (row["medicamento"], row["CESFAM"], int(L_i[row["medicamento"]])): row["inventario"]
    for _, row in i0_df.iterrows()
}

B_t = {
    int(row["semana"]): row["presupuesto"]
    for _, row in b_df.iterrows()
}

H_ct = {
    (row["CESFAM"], int(row["semana"])): row["capacidad"]
    for _, row in h_df.iterrows()
}

demanda_base = {
    (row["medicamento"], row["CESFAM"]): row["demanda"]
    for _, row in demanda_df.iterrows()
}

d_ictw = {}
for (i, c), d in demanda_base.items():
    for t in T:
        for w in Omega:
            d_ictw[(i, c, t, w)] = d * factor[w]

p_tw = {}
for t in T:
    if 1 <= t <= 8 or 49 <= t <= 52:
        p_tw[(t, "Baja")] = 0.50
        p_tw[(t, "Normal")] = 0.35
        p_tw[(t, "Alta")] = 0.15
    elif 25 <= t <= 38:
        p_tw[(t, "Baja")] = 0.10
        p_tw[(t, "Normal")] = 0.35
        p_tw[(t, "Alta")] = 0.55
    else:
        p_tw[(t, "Baja")] = 0.25
        p_tw[(t, "Normal")] = 0.50
        p_tw[(t, "Alta")] = 0.25

A_ikt = {}
for i in I:
    demanda_red = sum(demanda_base.get((i, c), 0) for c in C)
    for k in K:
        for t in T:
            trimestre = (t - 1) // 13 + 1
            factor_disp = 4.8 if trimestre == 3 else 6.4
            A_ikt[(i, k, t)] = factor_disp * demanda_red
