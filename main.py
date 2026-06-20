#Es necesaria una licencia de gurobi, no se puede la demo
import os
os.environ["GRB_LICENSE_FILE"] = os.path.abspath("gurobi.lic")

from gurobipy import GRB, Model, quicksum
from parametros import *

#Se va a multiplicar un ponderador a un parámetro a la vez (B, d y A) y se dejará el caso base

sensibilidad = [
    ("caso_base", "resultados_caso_base.txt", 1.00, 1.00, 1.00),

    ("B_t", "resultados_B_bajo.txt", 0.10, 1.00, 1.00),
    ("B_t", "resultados_B_alto.txt", 1.20, 1.00, 1.00),
    
    ("d_ictw", "resultados_d_bajo.txt", 1.00, 0.80, 1.00),
    ("d_ictw", "resultados_d_alto.txt", 1.00, 1.20, 1.00),
    
    ("A_ikt", "resultados_A_bajo.txt", 1.00, 1.00, 0.10),
    ("A_ikt", "resultados_A_alto.txt", 1.00, 1.00, 1.20),
]


for atributo, nombre_txt, p_B, p_d, p_A in sensibilidad:

    modelo = Model()
    modelo.setParam("TimeLimit", 60*30)
    modelo.setParam("OutputFlag", 0)

    #VARIABLES
    w_ikt = modelo.addVars(I, K, T, vtype=GRB.INTEGER, name="w_ikt")
    z_k = modelo.addVars(K, vtype=GRB.BINARY, name="z_k")
    x_ikcatw = modelo.addVars([(i, k, c, a, t, w) for i in I for k in K for c in C for a in A[i] for t in T for w in Omega], vtype=GRB.INTEGER, name="x_ikcatw")
    s_ikatw = modelo.addVars([(i, k, a, t, w) for i in I for k in K for a in A[i] for t in T for w in Omega], vtype=GRB.INTEGER, name="s_ikatw")
    y_icatw = modelo.addVars([(i, c, a, t, w) for i in I for c in C for a in A[i] for t in T for w in Omega], vtype=GRB.INTEGER, name="y_icatw")
    u_icatw = modelo.addVars([(i, c, a, t, w) for i in I for c in C for a in A[i] for t in T for w in Omega], vtype=GRB.INTEGER, name="u_icatw")
    q_ictw = modelo.addVars(I, C, T, Omega, vtype=GRB.INTEGER, name="q_ictw")
    e_ictw = modelo.addVars(I, C, T, Omega, vtype=GRB.INTEGER, name="e_ictw")
    vb_iktw = modelo.addVars(I, K, T, Omega, vtype=GRB.INTEGER, name="vb_iktw")
    vc_ictw = modelo.addVars(I, C, T, Omega, vtype=GRB.INTEGER, name="vc_ictw")
    modelo.update() 

    #RESTRICCIONES
    modelo.addConstrs((w_ikt[i, k, t] <= (A_ikt[i, k, t] * p_A) * z_k[k] for i in I for k in K for t in T), name="Activación de bodegas")

    modelo.addConstrs((q_ictw[i, c, t, w] <= (d_ictw[i, c, t, w] * p_d) for i in I for c in C for t in T for w in Omega), name="Cota de quiebre de stock")

    modelo.addConstrs((quicksum(y_icatw[i, c, a, t, w] for a in A[i]) <= Capc_ic[i, c] for c in C for i in I for t in T for w in Omega), name="Capacidad de almacenamiento en CESFAM")

    modelo.addConstrs((quicksum(s_ikatw[i, k, a, t, w] for a in A[i]) <= Capb_ik[i, k] * z_k[k] for k in K for i in I for t in T for w in Omega), name="Capacidad de almacenamiento en bodegas")

    modelo.addConstrs((quicksum(quicksum(CC_i[i] * w_ikt[i, k, t] for i in I) for k in K) + quicksum(quicksum(CE_i[i] * e_ictw[i, c, t, w] for i in I) for c in C) <= (B_t[t] * p_B) for t in T for w in Omega), name="Restricción presupuestaria") 

    modelo.addConstrs((quicksum(quicksum(quicksum(x_ikcatw[i, k, c, a, t, w] for a in A[i]) for c in C) for i in I) <= G_kt * z_k[k] for k in K for t in T for w in Omega), name="Capacidad de despacho")

    modelo.addConstrs((quicksum(quicksum(quicksum(x_ikcatw[i, k, c, a, t, w] for a in A[i]) for k in K) for i in I) + quicksum(e_ictw[i, c, t, w] for i in I) <= H_ct[c, t] for c in C for t in T for w in Omega), name="Capacidad de recepción en CESFAM")

    modelo.addConstrs((quicksum(quicksum(quicksum(CVb_i[i] * vb_iktw[i, k, t, w] for t in T) for k in K) for i in I) + quicksum(quicksum(quicksum(CVc_i[i] * vc_ictw[i, c, t, w] for t in T) for c in C) for i in I) <= Gamma for w in Omega), name="Límite de pérdida económica por vencimiento")

    modelo.addConstrs((quicksum(u_icatw[i, c, a, t, w] for a in A[i]) + e_ictw[i, c, t, w] + q_ictw[i, c, t, w] == (d_ictw[i, c, t, w] * p_d) for i in I for c in C for t in T for w in Omega), name="Satisfacción de la demanda")

    #Balances de inventario por edad
    modelo.addConstrs((y_icatw[i, c, a, t, w] == y_icatw[i, c, a + 1, t - 1, w] + quicksum(x_ikcatw[i, k, c, a, t, w] for k in K) - u_icatw[i, c, a, t, w] for i in I for c in C for w in Omega for a in A[i] if a < L_i[i] for t in T if t > 1), name="Balance de inventario en CESFAM")
    modelo.addConstrs((y_icatw[i, c, L_i[i], t, w] == quicksum(x_ikcatw[i, k, c, L_i[i], t, w] for k in K) - u_icatw[i, c, L_i[i], t, w] for i in I for c in C for w in Omega for t in T if t > 1), name="Balance de inventario en CESFAM edad maxima")
    modelo.addConstrs((y_icatw[i, c, a, 1, w] == I0_ica.get((i, c, a), 0) + quicksum(x_ikcatw[i, k, c, a, 1, w] for k in K) - u_icatw[i, c, a, 1, w] for i in I for c in C for a in A[i] for w in Omega), name="Balance de inventario inicial en CESFAM")
    modelo.addConstrs((s_ikatw[i, k, L_i[i], 1, w] == S0_ika.get((i, k, L_i[i]), 0) + w_ikt[i, k, 1] - quicksum(x_ikcatw[i, k, c, L_i[i], 1, w] for c in C) for i in I for k in K for w in Omega), name="Balance de inventario inicial en bodega")
    modelo.addConstrs((s_ikatw[i, k, a, 1, w] == S0_ika.get((i, k, a), 0) - quicksum(x_ikcatw[i, k, c, a, 1, w] for c in C) for i in I for k in K for w in Omega for a in A[i] if a < L_i[i]), name="Balance de inventario inicial en bodega por edad")
    modelo.addConstrs((s_ikatw[i, k, L_i[i], t, w] == w_ikt[i, k, t] - quicksum(x_ikcatw[i, k, c, L_i[i], t, w] for c in C) for i in I for k in K for w in Omega for t in T if t > 1), name="Balance de inventario en bodega por edad")
    modelo.addConstrs((s_ikatw[i, k, a, t, w] == s_ikatw[i, k, a + 1, t - 1, w] - quicksum(x_ikcatw[i, k, c, a, t, w] for c in C) for i in I for k in K for w in Omega for a in A[i] if a < L_i[i] for t in T if t > 1), name="Balance de inventario en bodega")

    #Vencimientos
    modelo.addConstrs((vc_ictw[i, c, t, w] == y_icatw[i, c, 1, t - 1, w] + quicksum(x_ikcatw[i, k, c, 1, t, w] for k in K) - u_icatw[i, c, 1, t, w] for i in I for c in C for t in T if t > 1 for w in Omega), name="Vencimiento de medicamentos en CESFAM")
    modelo.addConstrs((vc_ictw[i, c, 1, w] == I0_ica.get((i, c, 1), 0) + quicksum(x_ikcatw[i, k, c, 1, 1, w] for k in K) - u_icatw[i, c, 1, 1, w] for i in I for c in C for w in Omega), name="Vencimiento de medicamentos inicial en CESFAM")
    modelo.addConstrs((vb_iktw[i, k, t, w] == s_ikatw[i, k, 1, t - 1, w] - quicksum(x_ikcatw[i, k, c, 1, t, w] for c in C) for i in I for k in K for t in T if t > 1 for w in Omega), name="Vencimiento de medicamentos en bodega")
    modelo.addConstrs((vb_iktw[i, k, 1, w] == S0_ika.get((i, k, 1), 0) - quicksum(x_ikcatw[i, k, c, 1, 1, w] for c in C) for i in I for k in K for w in Omega), name="Vencimiento de medicamentos inicial en bodega")

    #Función objetivo
    f_o = quicksum(CC_i[i] * w_ikt[i, k, t] for t in T for i in I for k in K) + quicksum(F_k * z_k[k] for k in K) + quicksum(p_tw[t, w] * (quicksum(CD_ikc[i, k, c] * x_ikcatw[i, k, c, a, t, w] for i in I for k in K for c in C for a in A[i]) + quicksum(CE_i[i] * e_ictw[i, c, t, w] for i in I for c in C) + quicksum(CQ_i[i] * q_ictw[i, c, t, w] for i in I for c in C) + quicksum(CMb_ik[i, k] * s_ikatw[i, k, a, t, w] for i in I for k in K for a in A[i]) + quicksum(CMc_ic[i, c] * y_icatw[i, c, a, t, w] for i in I for c in C for a in A[i]) + quicksum(CVb_i[i] * vb_iktw[i, k, t, w] for i in I for k in K) + quicksum(CVc_i[i] * vc_ictw[i, c, t, w] for i in I for c in C)) for t in T for w in Omega)
    modelo.setObjective(f_o, GRB.MINIMIZE)

    modelo.optimize()

    #Acá se va a demorar bastante porque tiene generar 6 archivos, es decir, 6 veces se va a ejecutar las líneas siguientes
    if modelo.Status == GRB.OPTIMAL:
        with open(nombre_txt, "w", encoding="utf-8") as archivo:
            archivo.write(f"Instancia evaluada para el parametro: {atributo}\n")
            archivo.write(f"Valor Funcion Objetivo Z: {modelo.ObjVal}\n\n")

            #Bodegas activadas
            for k in K:
                if z_k[k].X > 0.5:
                    archivo.write(f"Bodega {k} activada.\n")

            #Compras programadas
            for i in I:
                for k in K:
                    for t in T:
                        val = w_ikt[i,k,t].X
                        if val > 1e-6:
                            archivo.write(f"Semana {t}: Compras programadas {i} en bodega {k} = {val:.2f}\n")

            #Despachos
            for i,k,c,a,t,w in x_ikcatw.keys():
                val = x_ikcatw[i,k,c,a,t,w].X
                if val > 1e-6:
                    archivo.write(f"Semana {t} [{w}]: Despacho {i} (edad {a}) desde {k} a {c} = {val:.2f}\n")

            #Compras de emergencia
            for i,c,t,w in e_ictw.keys():
                val = e_ictw[i,c,t,w].X
                if val > 1e-6:
                    archivo.write(f"Semana {t} [{w}]: Compra de emergencia {i} en {c} = {val:.2f}\n")

            #Quiebres
            for i,c,t,w in q_ictw.keys():
                val = q_ictw[i,c,t,w].X
                if val > 1e-6:
                    archivo.write(f"Semana {t} [{w}]: Demanda no satisfecha {i} en {c} = {val:.2f}\n")

            #Vencimientos
            for i,c,t,w in vc_ictw.keys():
                val = vc_ictw[i,c,t,w].X
                if val > 1e-6:
                    archivo.write(f"Semana {t} [{w}]: Medicamentos vencidos {i} en {c} = {val:.2f}\n")

            for i,k,t,w in vb_iktw.keys():
                val = vb_iktw[i,k,t,w].X
                if val > 1e-6:
                    archivo.write(f"Semana {t} [{w}]: Medicamentos vencidos {i} en bodega {k} = {val:.2f}\n")
        print(f"{nombre_txt} generado")           
    else:
        print(f"\nEl modelo finalizó con estado: {modelo.Status}")
        print(f"{nombre_txt} generado") 