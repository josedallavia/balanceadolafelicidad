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
    def __init__(self,U,M,V):
        self.cantidad_servicios = 0
        self.servicios = []
        self.cantidad_zonas = 0
        self.distancias = []
        self.var_idx = {} 
        self.U = U
        self.M = M
        self.V = V

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


def get_instance_data(U,M,V):
    #file_location = sys.argv[1].strip()
    file_location = "input_balanced_assignment.txt"
    instance = BalancedAssignmentInstance(U,M,V)
    instance.load(file_location)
    return instance
    

def add_constraint_matrix(my_problem, data):
    

    #Restricciones de y por arriba
    for j in range(data.U):
 
        ind = []
        values = []

        ind.append(data.var_idx[('min')])
        values.append(-1)
        
        for i in range(data.cantidad_servicios):
            for k in range(data.M):
                ind.append(data.var_idx[(i,j,k)])
                values.append(data.servicios[i].kilometros)
        
        row = [ind,values]
        
        my_problem.linear_constraints.add(lin_expr = [row], senses = ['G'], rhs = [0])
    
    
    #Restricciones de una unidad por servicio (una restriccion por cada servicio)
    
    for i in range(data.cantidad_servicios):
        ind = []
        values = []
        for j in range(data.U):
            for k in range (data.M):
                ind.append(data.var_idx[(i,j,k)])
                values.append(1)
        
        row = [ind,values]
        my_problem.linear_constraints.add(lin_expr = [row], senses = ['E'], rhs = [1])
    
    
    #Restriccion de un servicio por viaje de cada chofer (una restriccion por cada unidad-viaje)
    
    for j in range(data.U):
        for k in range(data.M):
            ind = []
            values = []
            for i in range(data.cantidad_servicios):
                ind.append(data.var_idx[(i,j,k)])
                values.append(1)
       
            row = [ind,values]
            #print(ind)
            my_problem.linear_constraints.add(lin_expr = [row], senses = ['L'], rhs = [1])
    
                
    
    #Restriccion de compatibilidad de asignaciones 
    for j in range(data.U):
      for k in range(data.M-1):
          for i1 in range(data.cantidad_servicios):
              for i2 in range(data.cantidad_servicios):
                  if i1 != i2:
                      #Calculamos la holgura que tiene el chofer para llegar de un servicio al otro
                      time_diff = (data.servicios[i2].horario_salida-data.servicios[i1].horario_llegada)
                      km_diff = data.distancias[data.servicios[i1].zona_llegada-1][data.servicios[i2].zona_salida-1]
                      
                      holgura = time_diff*(data.V/60)-km_diff
                      
                      #Si no hay tiempo suficiente para llegar de un punto al otro,
                      #restringimos esas variables 
                      if holgura < 0:
                          ind = [data.var_idx[(i1,j,k)],data.var_idx[(i2,j,k+1)]]
                          values = [1,1]
                          row = [ind, values]
                          my_problem.linear_constraints.add(lin_expr = [row], senses = ['L'], rhs = [1])
  

  
    
    #Restricción para que los viajes de un chofer sean asignados consecutivamente      
    for j in range(data.U):
        for k in range(data.M-1):
            ind = []
            values = []
            for i in range(data.cantidad_servicios):
                ind.append(data.var_idx[(i,j,k)])
                values.append(1)
            for i in range(data.cantidad_servicios):
                 ind.append(data.var_idx[(i,j,k+1)])
                 values.append(-1)
            
            row = [ind, values]
            my_problem.linear_constraints.add(lin_expr = [row], senses = ['G'], rhs = [0])
    

   
    
    
def populate_by_row(my_problem, data):
    
    
    obj = []
    var_type = []

  
    # var_cnt va a ser el valor que va llevando la cuenta de cuantas variables agregamos hasta el momento.
    var_cnt = 0
    
    
    # Generamos los indices de las variables MAIN y sus coeficientes en la fc objetivo
    for i in range(len(data.servicios)):
        for j in range(data.U):
            for k in range (data.M):
            # TODO Definimos el valor para (i,j,k). 
                data.var_idx[(i,j,k)] = var_cnt #defino como clave del diccionario la tupla (i,j,k)
                obj.append(0)
                var_type.append('B')
            # Incrementamos el proximo indice no usado..
                var_cnt += 1
    
    # Generamos los indices de las variables de la fc. OBJETIVO y sus coeficientes
    data.var_idx[('min')] = var_cnt
    obj.append(1)
    var_type.append('C')
    var_cnt += 1


    # Agregamos las variables.
    
    my_problem.variables.add( obj = obj, lb = [0]*len(obj),types = var_type) 

    # Seteamos direccion del problema
    my_problem.objective.set_sense(my_problem.objective.sense.maximize)

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
    i = 0        
    for var in data.var_idx:
        if x_variables[i] > TOLERANCE:
            print('x_' + str(var) + ':' , x_variables[i])
        i += 1


def main():
    
    #Seteamos variables exógenas
    U=15
    M=7
    #Velocidad promedio (km /hora).Eventualmente esto puede ser una fc de la hora del dia
    V = 50
    # Obtenemos los datos de la instancia.
    data = get_instance_data(U,M,V)
    
    # Definimos el problema de cplex.
    prob_lp = cplex.Cplex()
    
    # Armamos el modelo.
    populate_by_row(prob_lp,data)

    # Resolvemos el modelo.
    solve_lp(prob_lp,data)


if __name__ == '__main__':
    main()
