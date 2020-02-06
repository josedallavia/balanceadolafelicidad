import sys
import cplex

TOLERANCE =10e-6 

class Servicio:
    def __init__(self):
        self.horario_salida = 0
        self.horario_llegada = 0
        self.kilometros = 0
        self.punto_salida = ""
        self.punto_llegada = ""
        self.zona_salida = 0
        self.zona_llegada = 0
    
    def load(self, row):
        self.horario_salida = int(row[0])*60+int(row[1])
        self.horario_llegada = int(row[2])*60+int(row[3])
        self.kilometros = int(row[4])
        self.punto_salida = row[5]
        self.punto_llegada = row[6]
        self.zona_salida = int(row[7])
        self.zona_llegada = int(row[8])

class BalancedAssignmentInstance:
    def __init__(self,U,K):
        self.cantidad_servicios = 0
        self.servicios = []
        self.cantidad_zonas = 0
        self.distancias = []
        self.var_idx = {} 
        self.U = U
        self.K = K

    def load(self,filename):
        # Abrimos el archivo.
        f = open(filename)

        # Leemos la cantidad de servicios
        self.cantidad_servicios = int(f.readline())
        
        # Leemos cada uno de los servicios.
        self.servicios = []
        for i in range(self.cantidad_servicios):
            row = f.readline().split(' ')
            servicio = Servicio()
            servicio.load(row)
            self.servicios.append(servicio)
        
        # Leemos la cantidad de zonas
        self.cantidad_zonas = int(f.readline())
        
        # Leemos la matriz de distancias de zonas
        self.distancias = []
        for i in range(self.cantidad_zonas):
            row = f.readline().split(' ')
            self.distancias.append(list(map(int,row)))
        
        # Cerramos el archivo.
        f.close()


def get_instance_data(U,K):
    #file_location = sys.argv[1].strip()
    file_location = "input_balanced_assignment.txt"
    instance = BalancedAssignmentInstance(U,K)
    instance.load(file_location)
    return instance
    

def add_constraint_matrix(my_problem, data):
    
 
    #Restriccion de y por por arriba
    
    D = 0
    for i in data.servicios:
        D = D + i.kilometros
        

    for j in range(data.U):
 
        ind = []
        values = []

        ind.append(data.var_idx[(j)])
        values.append(1)
        
        for i in range(data.cantidad_servicios):
            for k in range(data.K-1):
                ind.append(data.var_idx(i,j,k))
                values.append(-1*data.servicios[i].kilometros)
        
        row = [ind,values]
        
        myprob.linear_constraints.add(lin_expr = [row], senses = ['G'], rhs = [-D/data.U])
   
    
    #Restricciones de y por abajo
    
    
    for j in range(data.U):
        # Generamos los indices (que al final tambien va a tener m posiciones).
        ind = []
        values = []
        # Agregamos en cada caso el indice de la variable que representa al arco (i,j), guardado en var_idx.
  
        ind.append(data.var_idx[(j)])
        values.append(1)
        
        for i in range(data.cantidad_servicios):
            for k in range(data.K-1):
                ind.append(data.var_idx[(i,j,k)])
                values.append(data.servicios[i].kilometros)
        
        row = [ind,values]
        
        myprob.linear_constraints.add(lin_expr = [row], senses = ['G'], rhs = [-D/data.U])
    
    
    #Restricciones de una unidad por servicio
    
    
    for i in range(data.cantidad_servicios):
        ind = []
        values = []
        for j in range(data.U):
            for k in range (data.K):
            ind.append(data.var_idx[(i,j,k)]
            values.append(1)
        
        row = [ind,values]
        myprob.linear_constraints.add(lin_expr = [row], senses = ['E'], rhs = [1])
    
        
    
    #Restriccion de un servicio por viaje de cada chofer
    
    for j in range(data.U):
        for k in range(data.K):
        ind = []
        values = []
        for i in range(data.cantidad_servicios):
                ind.append(data.var_idx[(i,j,k)]
                values.append(1)
       
        row = [ind,values]
        myprob.linear_constraints.add(lin_expr = [row], senses = ['L'], rhs = [1])
    
                
    
    #Restriccion de compatibilidad de asignaciones
    ind = []
    values = []
    for j in range(data.U):
        for k in range(data.K-1):
            for i1 in range(data.cantidad_servicios):
                for i2 in range(data.cantidad_servicios):
                    ind.append(data.var_idx[i1,i2,j,k])
                    time_diff = (data.servicios[i2].horario_salida-data.servicios[i1].horario_llegada)
                    holgura_km = time_diff*50-data.distancias[i1][i2]
                    
                    row = [ind, values]
                    myprob.linear_constraints.add(lin_expr = [row], senses = ['G'], rhs = [0])
                    
    
    #Restricciones para definir variables AUX
    
    for j in range(data.U):
        for k in range(data.K-1):
            for i1 in range(data.cantidad_servicios):
                for i2 in range(data.cantidad_servicios):
                    ind = []
                    ind.append(data.var_idx[i1,j,k])
                    ind.append(data.var_idx[i2,j,k])
                    ind.append(data.var_idx[i1,i2,j,k])
                    values = [1,1,-1]
                    
                    row = [ind, values]
                    myprob.linear_constraints.add(lin_expr = [row], senses = ['L'], rhs = [1])
                    
                    values = [-1,-1,2]
                    
                    row = [ind,values]
                    myprob.linear_constraints.add(lin_expr = [row], senses = ['L'], rhs = [0])
                    
   
    

def populate_by_row(my_problem, data):
    
    
    obj = []
    var_type = []

  
    # var_cnt va a ser el valor que va llevando la cuenta de cuantas variables agregamos hasta el momento.
    var_cnt = 0
    # Generamos los indices de las variables MAIN
    for i in range(data.servicios):
        for j in range(data.U):
            for k in range (data.K):
            # TODO Definimos el valor para (i,j,k). 
                data.var_idx[(i,j,k)] = var_cnt #defino como clave del diccionario la tupla (i,j,k)
                obj.append(0)
                var_type.append('B')
            # Incrementamos el proximo indice no usado..
                var_cnt += 1
    
    # Generamos los indices de las variables de las fc. OBJETIVO
    
    
    for j in range(data.U):
        data.var_idx[(j)] = var_cnt
        obj.append(1)
        var_type.append('C')
        var_cnt_obj += 1
        
    # Generamos los indices de las variables AUXILIARES
    
    for j in range(data.U):
        for k in range(data.K-1):
            for i1 in range(data.cantidad_servicios):
                for i2 in range(data.cantidad_servicios):
                    data.var_idx[(i1,i2,j,k)] = var_cnt
                    obj.append(0)
                    var_type.append('B')
                    var_cnt += 1


    # Definimos y agregamos las variables.
    
    my_problem.variables.add( obj = obj, lb = [0]*len(obj),types = var_types) 

    # Seteamos direccion del problema
    # ~ my_problem.objective.set_sense(my_problem.objective.sense.maximize)
    my_problem.objective.set_sense(my_problem.objective.sense.minimize)

    # Definimos las restricciones del modelo. Encapsulamos esto en una funcion. 
    add_constraint_matrix(my_problem, data)

    # Exportamos el LP cargado en myprob con formato .lp. 
    # Util para debug.
    my_problem.write('balanced_assignment.lp')

def solve_lp(my_problem, data):
    
    # Resolvemos el ILP.
    
    my_problem.solve()

    # Obtenemos informacion de la solucion. Esto lo hacemos a traves de 'solution'. 
    x_variables = my_problem.solution.get_values()
    objective_value = my_problem.solution.get_objective_value()
    status = my_problem.solution.get_status()
    status_string = my_problem.solution.get_status_string(status_code = status)

    print('Funcion objetivo: ',objective_value)
    print('Status solucion: ',status_string,'(' + str(status) + ')')

    # Imprimimos las variables usadas.
    for i in range(len(x_variables)):
        # Tomamos esto como valor de tolerancia, por cuestiones numericas.
        if x_variables[i] > TOLERANCE:
            print('x_' + str(data.items[i].index) + ':' , x_variables[i])

def main():
    
    # Obtenemos los datos de la instancia.
    U=20
    K=10
    data = get_instance_data(U,K)
    
    # Definimos el problema de cplex.
    prob_lp = cplex.Cplex()
    
    # Armamos el modelo.
    populate_by_row(prob_lp,data)

    # Resolvemos el modelo.
    solve_lp(prob_lp,data)


if __name__ == '__main__':
    main()
