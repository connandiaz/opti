from gurobipy import GRB, Model
from gurobipy import quicksum
from parametros import *

modelo = Model()
modelo.setParam("TimeLimit", 60*30)

I = range(1, 30 + 1) #Conjunto de medicamentos de alto uso
C = range (1, 8 + 1) #Conjunto de centros CESFAM de la comuna de Puente Alto
K = range(1, 4 + 1) #Conjunto de bodegas o puntos de almacenamiento diferenciados
T = range (1, 52 + 1) #Conjunto de períodos en semanas del horizonte de planificación
A = range(1, I + 1) #Conjunto de edades o semanas restantes de vida útil del medicamento i
Omega = range(1, 4 + 1) #Conjunto de escenarios de demanda

#Variables de decisión
w_ikt = modelo.addVars(I, K, T, vtype=GRB.INTEGER, name="w_ikt")
z_k = modelo.addVars(K, vtype=GRB.BINARY, name="z_k")
x_ikatw = modelo.addVars(I, K, A, T, Omega, vtype=GRB.INTEGER, name="x_ikatw")
s_ikatw = modelo.addVars(I, K, A, T, Omega, vtype=GRB.INTEGER, name="s_ikatw")
y_icatw = modelo.addVars(I, C, A, T, Omega, vtype=GRB.INTEGER, name="y_icatw")
u_icatw = modelo.addVars(I, C, A, T, Omega, vtype=GRB.INTEGER, name="u_icatw")
q_ictw = modelo.addVars(I, C, T, Omega, vtype=GRB.INTEGER, name="q_ictw")
e_ictw = modelo.addVars(I, C, T, Omega, vtype=GRB.INTEGER, name="e_ictw")
vb_iktw = modelo.addVars(I, K, T, Omega, vtype=GRB.INTEGER, name="vb_iktw")
vc_ictw = modelo.addVars(I, C, T, Omega, vtype=GRB.INTEGER, name="vc_ictw")

modelo.update() #para evitar errores con las restricciones a continuación

#Restricciones
modelo.addConstrs((w_ikt <= A_ikt * z_k for i in I for k in K for t in T), name="Activación de bodegas")

modelo.addConstrs((q_ictw <= d_ictw for i in I for c in C for t in T for w in Omega), name="Cota de quiebre de stock")

modelo.addConstrs((quicksum(y_icatw for a in A) <= Capc_ic for k in K for i in I for t in T for w in Omega), name="Capacidad de almacenamiento en CESFAM")

modelo.addConstrs((quicksum(s_ikatw for a in A) <= Capb_ik * z_k for k in K for i in I for t in T for w in Omega), name="Capacidad de almacenamiento en bodegas")

modelo.addConstrs((quicksum(quicksum(CC_i * w_ikt for i in I) for k in K) + quicksum(quicksum(CE_i * e_ictw for i in I) for c in C) <= B_t for t in T for w in Omega), name="Restricción presupuestaria") 

modelo.addConstrs((quicksum(quicksum(quicksum(x_ikatw for a in A) for c in C) for i in I) <= G_kt * z_k for k in K for t in T for w in Omega), name="Capacidad de despacho")

modelo.addConstrs((quicksum(quicksum(quicksum(x_ikatw for a in A) for k in K) for i in I) + quicksum(e_ictw for i in I) <= H_ct for c in C for t in T for w in Omega), name="Capacidad de recepción en CESFAM")

modelo.addConstrs((quicksum(quicksum(quicksum(CVb_i * vb_iktw for t in T) for k in K) for i in I) + quicksum(quicksum(quicksum(CVc_i * vc_ictw for t in T) for c in C) for i in I) <= Gamma for w in Omega), name="Límite de pérdida económica por vencimiento")

modelo.addConstrs((quicksum(u_icatw + e_ictw + q_ictw for a in A) == d_ictw for i in I for c in C for t in T for w in Omega), name="Satisfacción de la demanda")

#Balance de inventario en CESFAM
modelo.addConstrs((y_icatw == y_icatw[i, c, a + 1, t - 1, w] + quicksum(x_ikatw - u_icatw for k in K) for i in I for c in C for w in Omega for a in A if a < L_i for t in T if t > 1), name="Balance de inventario en CESFAM")

modelo.addConstrs((y_icatw[i, c, a, 1, w] == I0_ica + quicksum(x_ikatw[i, k, a, 1, w] - u_icatw[i, c, a, 1, w] for k in K) for a in A for i in I for c in C for w in Omega), name="Balance de inventario inicial en CESFAM")

#Balance de inventario en bodega por edad
