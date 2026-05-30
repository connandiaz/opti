from gurobipy import GRB, Model, quicksum
from parametros import *

modelo = Model()
modelo.setParam("TimeLimit", 60*30)

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

modelo.addConstrs((w_ikt[i, k, t] <= A_ikt[i, k, t] * z_k[k] for i in I for k in K for t in T), name="Activación de bodegas")

modelo.addConstrs((q_ictw[i, c, t, w] <= d_ictw[i, c, t, w] for i in I for c in C for t in T for w in Omega), name="Cota de quiebre de stock")

modelo.addConstrs((quicksum(y_icatw[i, c, a, t, w] for a in A[i]) <= Capc_ic[i, c] for c in C for i in I for t in T for w in Omega), name="Capacidad de almacenamiento en CESFAM")

modelo.addConstrs((quicksum(s_ikatw[i, k, a, t, w] for a in A[i]) <= Capb_ik[i, k] * z_k[k] for k in K for i in I for t in T for w in Omega), name="Capacidad de almacenamiento en bodegas")

modelo.addConstrs((quicksum(quicksum(CC_i[i] * w_ikt[i, k, t] for i in I) for k in K) + quicksum(quicksum(CE_i[i] * e_ictw[i, c, t, w] for i in I) for c in C) <= B_t[t] for t in T for w in Omega), name="Restricción presupuestaria") 

modelo.addConstrs((quicksum(quicksum(quicksum(x_ikcatw[i, k, c, a, t, w] for a in A[i]) for c in C) for i in I) <= G_kt * z_k[k] for k in K for t in T for w in Omega), name="Capacidad de despacho")

modelo.addConstrs((quicksum(quicksum(quicksum(x_ikcatw[i, k, c, a, t, w] for a in A[i]) for k in K) for i in I) + quicksum(e_ictw[i, c, t, w] for i in I) <= H_ct[c, t] for c in C for t in T for w in Omega), name="Capacidad de recepción en CESFAM")

modelo.addConstrs((quicksum(quicksum(quicksum(CVb_i[i] * vb_iktw[i, k, t, w] for t in T) for k in K) for i in I) + quicksum(quicksum(quicksum(CVc_i[i] * vc_ictw[i, c, t, w] for t in T) for c in C) for i in I) <= Gamma for w in Omega), name="Límite de pérdida económica por vencimiento")

modelo.addConstrs((quicksum(u_icatw[i, c, a, t, w] for a in A[i]) + e_ictw[i, c, t, w] + q_ictw[i, c, t, w] == d_ictw[i, c, t, w] for i in I for c in C for t in T for w in Omega), name="Satisfacción de la demanda")

modelo.addConstrs((quicksum(u_icatw[i, c, a, t, w] for a in A[i] for c in C for t in T) >= alpha_i[i] * quicksum(d_ictw[i, c, t, w] for c in C for t in T) for i in I for w in Omega), name="Nivel de servicio minimo")

#Balance de inventario en CESFAM
modelo.addConstrs((y_icatw[i, c, a, t, w] == y_icatw[i, c, a + 1, t - 1, w] + quicksum(x_ikcatw[i, k, c, a, t, w] - u_icatw[i, c, a, t, w] for k in K) for i in I for c in C for w in Omega for a in A[i] if a < L_i[i] for t in T if t > 1), name="Balance de inventario en CESFAM")

modelo.addConstrs((y_icatw[i, c, a, 1, w] == I0_ica.get((i, c, a), 0) + quicksum(x_ikcatw[i, k, c, a, 1, w] - u_icatw[i, c, a, 1, w] for k in K) for i in I for c in C for a in A[i] for w in Omega), name="Balance de inventario inicial en CESFAM")

#Balance de inventario en bodega por edad
modelo.addConstrs((s_ikatw[i, k, L_i[i], 1, w] == S0_ika.get((i, k, L_i[i]), 0) + w_ikt[i, k, 1] - quicksum(x_ikcatw[i, k, c, L_i[i], 1, w] for c in C) for i in I for k in K for w in Omega), name="Balance de inventario inicial en bodega")

modelo.addConstrs((s_ikatw[i, k, a, 1, w] == S0_ika.get((i, k, a), 0) - quicksum(x_ikcatw[i, k, c, a, 1, w] for c in C) for i in I for k in K for w in Omega for a in A[i] if a < L_i[i]), name="Balance de inventario inicial en bodega por edad")

modelo.addConstrs((s_ikatw[i, k, L_i[i], t, w] == w_ikt[i, k, t] - quicksum(x_ikcatw[i, k, c, L_i[i], t, w] for c in C) for i in I for k in K for w in Omega for t in T if t > 1), name="Balance de inventario en bodega por edad")

modelo.addConstrs((s_ikatw[i, k, a, t, w] == s_ikatw[i, k, a + 1, t - 1, w] - quicksum(x_ikcatw[i, k, c, a, t, w] for c in C) for i in I for k in K for w in Omega for a in A[i] if a < L_i[i] for t in T if t > 1), name="Balance de inventario en bodega")

#Vencimiento de medicamentos en bodega
modelo.addConstrs((vc_ictw[i, c, t, w] == y_icatw[i, c, 1, t - 1, w] + quicksum(x_ikcatw[i, k, c, 1, t, w] for k in K) - u_icatw[i, c, 1, t, w] for i in I for c in C for t in T if t > 1 for w in Omega), name="Vencimiento de medicamentos en CESFAM"  )

modelo.addConstrs((vc_ictw[i, c, 1, w] == I0_ica.get((i, c, 1), 0) + quicksum(x_ikcatw[i, k, c, 1, 1, w] for k in K) - u_icatw[i, c, 1, 1, w] for i in I for c in C for w in Omega), name="Vencimiento de medicamentos inicial en CESFAM")

modelo.addConstrs((vb_iktw[i, k, t, w] == s_ikatw[i, k, 1, t - 1, w] - quicksum(x_ikcatw[i, k, c, 1, t, w] for c in C) for i in I for k in K for t in T if t > 1 for w in Omega), name="Vencimiento de medicamentos en bodega")

modelo.addConstrs((vb_iktw[i, k, 1, w] == S0_ika.get((i, k, 1), 0) - quicksum(x_ikcatw[i, k, c, 1, 1, w] for c in C) for i in I for k in K for w in Omega), name="Vencimiento de medicamentos inicial en bodega")

#Función objetivo
f_o = quicksum(CC_i[i] * w_ikt[i, k, t] for t in T for i in I for k in K) + quicksum(F_k * z_k[k] for k in K) + quicksum(p_tw[t, w] * (quicksum(CD_ikc[i, k, c] * x_ikcatw[i, k, c, a, t, w] for i in I for k in K for c in C for a in A[i]) + quicksum(CE_i[i] * e_ictw[i, c, t, w] for i in I for c in C) + quicksum(CQ_i[i] * q_ictw[i, c, t, w] for i in I for c in C) + quicksum(CMb_ik[i, k] * s_ikatw[i, k, a, t, w] for i in I for k in K for a in A[i]) + quicksum(CMc_ic[i, c] * y_icatw[i, c, a, t, w] for i in I for c in C for a in A[i]) + quicksum(CVb_i[i] * vb_iktw[i, k, t, w] for i in I for k in K) + quicksum(CVc_i[i] * vc_ictw[i, c, t, w] for i in I for c in C)) for t in T for w in Omega)
modelo.setObjective(f_o, GRB.MINIMIZE)

modelo.optimize()

if modelo.Status == GRB.OPTIMAL:
    print("\n" + "="*40)
    print("      ¡OPTIMIZACIÓN EXITOSA!")
    print("="*40)
    print(f"Costo Total Mínimo (Z): ${modelo.ObjVal:,.2f}")
    
    print("\n--- Bodegas Activas ---")
    for k in K:
        if z_k[k].X > 0.5:
            print(f"-> Bodega {k} está ACTIVA")
            
    print("\n--- Total de Compras Programadas ---")
    total_w = sum(w_ikt[i, k, t].X for i in I for k in K for t in T)
    print(f"Unidades totales compradas: {total_w:,.0f}")
    
    print("\n--- Total de Compras de Emergencia ---")
    total_e = sum(e_ictw[i, c, t, w].X for i in I for c in C for t in T for w in Omega)
    print(f"Unidades totales de emergencia: {total_e:,.0f}")

    print("\n--- Total de Faltantes (Quiebres) ---")
    total_q = sum(q_ictw[i, c, t, w].X for i in I for c in C for t in T for w in Omega)
    print(f"Unidades totales no suministradas: {total_q:,.0f}")
    print("="*40)
else:
    print(f"\nEl modelo finalizó con estado: {modelo.Status}")
